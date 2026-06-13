"""
Mundial 2026 - Predictor de Marcadores
Implementacion en Python puro (sin dependencias externas).

Uso rapido:
  python3 predictor.py                         # Menu interactivo
  python3 predictor.py --grupo A               # Predice grupo completo
  python3 predictor.py --partido "USA" "Panama"
  python3 predictor.py --todos                 # Predice 72 partidos de grupos
  python3 predictor.py --variables             # Explica variables del modelo
"""

import math
import json
import sys
import argparse
from pathlib import Path
from itertools import combinations

# ─────────────────────────────────────────────────────────────────────────────
# MODELO POISSON BIVARIANTE (Dixon-Coles simplificado, pure Python)
# ─────────────────────────────────────────────────────────────────────────────

def poisson_pmf(k: int, lam: float) -> float:
    """P(X = k) para distribucion de Poisson con media lam."""
    if lam <= 0 or k < 0:
        return 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def dixon_coles_correction(i: int, j: int, mu_h: float, mu_a: float, rho: float) -> float:
    """Corrección DC para resultados de baja puntuacion (0-0, 1-0, 0-1, 1-1)."""
    if i == 0 and j == 0:
        return 1.0 - mu_h * mu_a * rho
    elif i == 1 and j == 0:
        return 1.0 + mu_a * rho
    elif i == 0 and j == 1:
        return 1.0 + mu_h * rho
    elif i == 1 and j == 1:
        return 1.0 - rho
    return 1.0

def score_matrix(mu_h: float, mu_a: float, rho: float = -0.13,
                 max_goals: int = 7) -> list[list[float]]:
    """
    Calcula la matriz (max_goals+1 x max_goals+1) de probabilidades.
    matrix[i][j] = P(home=i, away=j)
    """
    matrix = []
    for i in range(max_goals + 1):
        row = []
        for j in range(max_goals + 1):
            p = poisson_pmf(i, mu_h) * poisson_pmf(j, mu_a)
            tau = dixon_coles_correction(i, j, mu_h, mu_a, rho)
            p *= max(tau, 1e-10)
            row.append(max(p, 0.0))
        matrix.append(row)

    # Renormalizar
    total = sum(p for row in matrix for p in row)
    if total > 0:
        matrix = [[p / total for p in row] for row in matrix]
    return matrix

def outcome_probs(matrix: list[list[float]]) -> tuple[float, float, float]:
    """Retorna (P_home_win, P_draw, P_away_win)."""
    n = len(matrix)
    p_home, p_draw, p_away = 0.0, 0.0, 0.0
    for i in range(n):
        for j in range(n):
            p = matrix[i][j]
            if i > j:
                p_home += p
            elif i == j:
                p_draw += p
            else:
                p_away += p
    return p_home, p_draw, p_away

def most_likely_score(matrix: list[list[float]]) -> tuple[int, int, float]:
    """Retorna (home_goals, away_goals, prob) del marcador mas probable."""
    best = (0, 0, 0.0)
    for i, row in enumerate(matrix):
        for j, p in enumerate(row):
            if p > best[2]:
                best = (i, j, p)
    return best

def expected_goals(matrix: list[list[float]]) -> tuple[float, float]:
    """Calcula goles esperados (E[home], E[away]) desde la matriz."""
    n = len(matrix)
    eh = sum(i * matrix[i][j] for i in range(n) for j in range(n))
    ea = sum(j * matrix[i][j] for i in range(n) for j in range(n))
    return eh, ea

# ─────────────────────────────────────────────────────────────────────────────
# CALCULO DE PARAMETROS (mu_h, mu_a) A PARTIR DE VARIABLES PRE-TORNEO
# ─────────────────────────────────────────────────────────────────────────────

# Factores de escala calibrados con mundiales 2014-2022 (media ~2.64 goles/partido)
BASE_GOALS = 1.25        # Goles base por partido en torneo neutral
ELO_SCALE  = 400.0       # Diferencia Elo que corresponde a ~1.5x en fuerza
XG_WEIGHT  = 0.45        # Peso del xG promedio en el calculo
FORM_WEIGHT = 0.20       # Peso de la forma reciente
CLASIF_WEIGHT = 0.20     # Peso del rendimiento en clasificatorias
ELO_WEIGHT = 0.15        # Peso del Elo (ya esta implicitamente en lo demas)

def elo_win_prob(elo_a: float, elo_b: float) -> float:
    """Probabilidad de victoria de A vs B segun formula Elo estandar."""
    return 1.0 / (1.0 + 10 ** ((elo_b - elo_a) / 400.0))

def forma_score(puntos_ultimos10: list[int]) -> float:
    """
    Calcula puntaje de forma con decaimiento exponencial.
    Partidos mas recientes pesan el doble que los mas lejanos.
    Normalizado al rango [0, 1].
    """
    n = len(puntos_ultimos10)
    total_weight = 0.0
    weighted_pts = 0.0
    for i, pts in enumerate(puntos_ultimos10):
        # peso exponencial: el mas reciente (ultimo en la lista) pesa mas
        w = math.exp(0.15 * i)
        weighted_pts += pts * w
        total_weight += 3 * w  # maximo posible = 3 puntos * peso
    return weighted_pts / total_weight if total_weight > 0 else 0.5

def compute_expected_goals(equipo: dict, rival: dict) -> tuple[float, float]:
    """
    Calcula mu (goles esperados) para equipo vs rival en cancha neutral.

    Variables utilizadas:
      1. xG promedio en clasificatoria (calidad de ocasiones creadas)
      2. xGA del rival (solidez defensiva del contrario)
      3. Forma reciente ponderada exponencialmente
      4. Puntos por partido en clasificatoria (rendimiento en competencia)
      5. Diferencial Elo (fortaleza relativa global)
    """
    # --- xG base: media geometrica de mi ataque y su defensa ---
    ataque_base = (equipo["xg_prom"] + rival["xga_prom"]) / 2.0

    # --- Ajuste por forma reciente ---
    mi_forma = forma_score(equipo["forma_ultimos10"])
    forma_adj = 0.85 + (mi_forma * 0.30)  # rango ~[0.85, 1.15]

    # --- Ajuste por rendimiento en clasificatoria (PPG normalizado 0-3) ---
    ppg_norm = equipo["clasif_ppg"] / 3.0
    clasif_adj = 0.88 + (ppg_norm * 0.24)  # rango ~[0.88, 1.12]

    # --- Diferencial Elo: ajuste multiplicativo ---
    elo_diff = equipo["elo"] - rival["elo"]
    # Cada 100 puntos Elo ≈ 5% mas de goles
    elo_adj = math.exp(elo_diff / 2000.0)

    mu = ataque_base * forma_adj * clasif_adj * elo_adj
    return round(mu, 4)

def predict_match(t1_nombre: str, t1: dict, t2_nombre: str, t2: dict,
                  rho: float = -0.13) -> dict:
    """Predice un partido entre dos equipos. Cancha neutral (Mundial)."""
    mu_h = compute_expected_goals(t1, t2)
    mu_a = compute_expected_goals(t2, t1)

    matrix = score_matrix(mu_h, mu_a, rho=rho)
    ph, pd, pa = outcome_probs(matrix)
    g_h, g_a, p_score = most_likely_score(matrix)
    eh, ea = expected_goals(matrix)

    # Top 5 marcadores
    flat = [(i, j, matrix[i][j])
            for i in range(len(matrix))
            for j in range(len(matrix[0]))]
    flat.sort(key=lambda x: -x[2])
    top5 = flat[:5]

    # Penaltis: probabilidad ajustada por Elo para rondas KO
    elo_ratio = elo_win_prob(t1["elo"], t2["elo"])
    p1_ko = ph + pd * elo_ratio
    p2_ko = pa + pd * (1 - elo_ratio)

    return {
        "team1": t1_nombre, "team2": t2_nombre,
        "mu1": mu_h, "mu2": mu_a,
        "p_win1": ph, "p_draw": pd, "p_win2": pa,
        "expected": (round(eh, 2), round(ea, 2)),
        "best_score": (g_h, g_a), "best_score_prob": p_score,
        "top5_scores": top5,
        "p_ko_win1": p1_ko, "p_ko_win2": p2_ko,
        "predicted_winner": (t1_nombre if ph > pa and ph > pd
                             else t2_nombre if pa > ph and pa > pd
                             else "Empate"),
        "ko_winner": t1_nombre if p1_ko > p2_ko else t2_nombre,
    }

# ─────────────────────────────────────────────────────────────────────────────
# CARGA DE DATOS
# ─────────────────────────────────────────────────────────────────────────────

def load_teams() -> dict:
    path = Path(__file__).parent / "data" / "wc2026" / "equipos_wc2026.json"
    with open(path) as f:
        data = json.load(f)
    return data["equipos"]

def load_groups(equipos: dict) -> dict[str, list[str]]:
    grupos: dict[str, list[str]] = {}
    for nombre, info in equipos.items():
        g = info["grupo"]
        grupos.setdefault(g, []).append(nombre)
    return {k: sorted(v) for k, v in sorted(grupos.items())}

# ─────────────────────────────────────────────────────────────────────────────
# DISPLAY
# ─────────────────────────────────────────────────────────────────────────────

LINE = "─" * 70

def print_header(titulo: str):
    print(f"\n{'═'*70}")
    print(f"  {titulo}")
    print(f"{'═'*70}")

def print_match_full(pred: dict, equipos: dict):
    t1, t2 = pred["team1"], pred["team2"]
    e1, e2 = equipos[t1], equipos[t2]

    print(f"\n{LINE}")
    print(f"  {t1.upper():<30} vs  {t2.upper()}")
    print(LINE)
    print(f"  {'Variable':<35} {'':>12} {'':>12}")
    print(f"  {'Elo rating':<35} {e1['elo']:>12,} {e2['elo']:>12,}")
    print(f"  {'FIFA Ranking':<35} {'#'+str(e1['fifa_rank']):>12} {'#'+str(e2['fifa_rank']):>12}")
    print(f"  {'xG prom. (clasif.)':<35} {e1['xg_prom']:>12.2f} {e2['xg_prom']:>12.2f}")
    print(f"  {'xGA prom. (clasif.)':<35} {e1['xga_prom']:>12.2f} {e2['xga_prom']:>12.2f}")
    print(f"  {'PPG clasificatoria':<35} {e1['clasif_ppg']:>12.2f} {e2['clasif_ppg']:>12.2f}")
    forma1 = forma_score(e1["forma_ultimos10"])
    forma2 = forma_score(e2["forma_ultimos10"])
    print(f"  {'Forma reciente [0-1]':<35} {forma1:>12.3f} {forma2:>12.3f}")
    print(f"  {'Goles esperados (mu)':<35} {pred['mu1']:>12.3f} {pred['mu2']:>12.3f}")
    print()
    print(f"  PROBABILIDADES DE RESULTADO:")
    bar_w = int(pred['p_win1'] * 30)
    bar_d = int(pred['p_draw'] * 30)
    bar_a = int(pred['p_win2'] * 30)
    print(f"  Victoria {t1[:20]:<20}: {pred['p_win1']*100:>5.1f}%  {'█'*bar_w}")
    print(f"  Empate                         : {pred['p_draw']*100:>5.1f}%  {'█'*bar_d}")
    print(f"  Victoria {t2[:20]:<20}: {pred['p_win2']*100:>5.1f}%  {'█'*bar_a}")
    print()
    print(f"  Goles esperados    : {pred['expected'][0]:.2f} - {pred['expected'][1]:.2f}")
    print(f"  Marcador probable  : {pred['best_score'][0]}-{pred['best_score'][1]}"
          f"  ({pred['best_score_prob']*100:.1f}%)")
    print(f"  RESULTADO PREDICHO : {pred['predicted_winner'].upper()}")
    print()
    print(f"  TOP 5 MARCADORES MAS PROBABLES:")
    print(f"  {'Marcador':^12} {'Prob':>8}")
    print(f"  {'-'*22}")
    for i, j, p in pred["top5_scores"]:
        print(f"  {t1[:6]}:{i} - {t2[:6]}:{j}   {p*100:>6.2f}%")

def print_match_compact(pred: dict) -> str:
    t1, t2 = pred["team1"], pred["team2"]
    score = f"{pred['best_score'][0]}-{pred['best_score'][1]}"
    winner = pred["predicted_winner"]
    ph = pred["p_win1"] * 100
    pd_ = pred["p_draw"] * 100
    pa = pred["p_win2"] * 100
    return (f"  {t1:<22} {score}  {t2:<22} "
            f"| {ph:4.1f}% / {pd_:4.1f}% / {pa:4.1f}%"
            f"  -> {winner}")

def simulate_group(grupo: str, equipos: dict) -> dict:
    """Simula el grupo y devuelve tabla de posiciones + partidos."""
    equipos_grupo = {n: equipos[n] for n in equipos
                     if equipos[n]["grupo"] == grupo}
    nombres = list(equipos_grupo.keys())

    pts = {n: 0 for n in nombres}
    gf  = {n: 0 for n in nombres}
    gc  = {n: 0 for n in nombres}
    partidos = []

    for n1, n2 in combinations(nombres, 2):
        pred = predict_match(n1, equipos_grupo[n1], n2, equipos_grupo[n2])
        g1, g2 = pred["best_score"]

        # Ajuste de consistencia: si hay ganador predicho, verificar marcador
        if pred["predicted_winner"] == n1 and g1 <= g2:
            g1 = g2 + 1
        elif pred["predicted_winner"] == n2 and g2 <= g1:
            g2 = g1 + 1

        gf[n1] += g1; gc[n1] += g2
        gf[n2] += g2; gc[n2] += g1

        if g1 > g2:
            pts[n1] += 3
        elif g2 > g1:
            pts[n2] += 3
        else:
            pts[n1] += 1; pts[n2] += 1

        partidos.append({
            "t1": n1, "t2": n2, "g1": g1, "g2": g2,
            "ph": round(pred["p_win1"] * 100, 1),
            "pd": round(pred["p_draw"] * 100, 1),
            "pa": round(pred["p_win2"] * 100, 1),
        })

    # Ordenar tabla
    tabla = sorted(nombres,
                   key=lambda n: (pts[n], gf[n]-gc[n], gf[n]),
                   reverse=True)
    return {"partidos": partidos, "tabla": tabla,
            "pts": pts, "gf": gf, "gc": gc}

def print_group(grupo: str, equipos: dict):
    resultado = simulate_group(grupo, equipos)
    print_header(f"GRUPO {grupo}")

    print("\n  PARTIDOS:")
    print(f"  {'Local':<22} {'Mar':^5} {'Visitante':<22} | {'L%':>5} {'E%':>5} {'V%':>5}")
    print(f"  {'-'*70}")
    for p in resultado["partidos"]:
        marcador = f"{p['g1']}-{p['g2']}"
        print(f"  {p['t1']:<22} {marcador:^5} {p['t2']:<22} "
              f"| {p['ph']:>4.1f} {p['pd']:>4.1f} {p['pa']:>4.1f}")

    print(f"\n  TABLA DE POSICIONES:")
    print(f"  {'Pos':<4} {'Equipo':<22} {'PJ':>3} {'Pts':>4} {'GF':>4} {'GC':>4} {'DG':>4}")
    print(f"  {'-'*50}")
    for i, nombre in enumerate(resultado["tabla"]):
        califica = "✓" if i < 2 else " "
        dg = resultado["gf"][nombre] - resultado["gc"][nombre]
        print(f"  {califica}{i+1:<3} {nombre:<22} {'3':>3} "
              f"{resultado['pts'][nombre]:>4} "
              f"{resultado['gf'][nombre]:>4} "
              f"{resultado['gc'][nombre]:>4} "
              f"{dg:>4}")
    print("\n  ✓ = Clasificado directo (top 2)")

def print_all_groups(equipos: dict):
    """Predice los 72 partidos de la fase de grupos."""
    grupos = sorted(set(e["grupo"] for e in equipos.values()))
    print_header("MUNDIAL 2026 — PREDICCION FASE DE GRUPOS (72 PARTIDOS)")

    total_partidos = 0
    for g in grupos:
        print_group(g, equipos)
        total_partidos += 6  # 4 equipos => 6 partidos por grupo

    print(f"\n{'═'*70}")
    print(f"  Total partidos de grupos predichos: {total_partidos}")
    print(f"{'═'*70}")

def print_variables():
    """Explica las variables del modelo y su fuente de datos."""
    print_header("VARIABLES DEL MODELO — MUNDIAL 2026")
    variables = [
        ("xG promedio (xg_prom)", "Alto",
         "Expected Goals en clasificatoria. Mide la CALIDAD de las ocasiones "
         "creadas, no solo cuantos goles se anotaron. Un xG alto con pocos "
         "goles reales indica mala definicion pero buen juego.",
         "fbref.com/en/country/players/ | StatsBomb Open Data (GitHub)"),

        ("xGA promedio (xga_prom)", "Alto",
         "Expected Goals Against. Solidez defensiva REAL del equipo. "
         "Un xGA bajo indica que el rival genera pocas/malas ocasiones.",
         "fbref.com | StatsBomb Open Data"),

        ("Forma reciente (forma_ultimos10)", "Medio-Alto",
         "Puntos obtenidos en los ultimos 10 partidos con peso exponencial: "
         "el partido mas reciente vale ~2x el mas lejano. Detecta tendencias.",
         "rsssf.org | kaggle: international-football-results"),

        ("PPG clasificatoria (clasif_ppg)", "Medio-Alto",
         "Puntos por partido en las eliminatorias del Mundial 2026. "
         "Refleja nivel competitivo real contra selecciones de su region.",
         "rsssf.org/tables/ — descarga por confederacion"),

        ("Rating Elo (elo)", "Medio",
         "Sistema de rating tipo ajedrez. Calibrado con resultados historicos. "
         "Diferencia de 200 pts Elo => probabilidad ~74% para el favorito.",
         "eloratings.net/World.tsv — descarga directa sin registro"),

        ("Ranking FIFA (fifa_rank)", "Bajo-Medio",
         "Ranking oficial FIFA. Menos preciso que Elo porque premia "
         "cantidad de partidos. Util para contexto y agrupaciones.",
         "fifa.com/fifa-world-ranking/men"),

        ("Valor de plantilla (valor_plantilla_M)", "Referencia",
         "Valor de mercado total en millones de euros. Proxy de calidad "
         "individual. Correlacion moderada con resultado en torneo.",
         "transfermarkt.com/nationalmannschaft/"),
    ]

    print(f"\n  {'Variable':<35} {'Peso':<12} {'Fuente'}")
    print(f"  {'-'*68}")
    for var, peso, desc, fuente in variables:
        print(f"\n  [{peso}] {var}")
        # Wrap descripcion
        palabras = desc.split()
        linea = "    "
        for p in palabras:
            if len(linea) + len(p) > 68:
                print(linea)
                linea = "    " + p + " "
            else:
                linea += p + " "
        print(linea)
        print(f"    FUENTE: {fuente}")

    print(f"\n{'═'*70}")
    print("  FORMULA DEL MODELO (mu = goles esperados por equipo):")
    print()
    print("  mu = ((xG_i + xGA_j) / 2)              <- calidad ofensiva vs defensiva")
    print("       × (0.85 + forma_i × 0.30)          <- ajuste por forma reciente")
    print("       × (0.88 + PPG_norm_i × 0.24)       <- ajuste por clasificatoria")
    print("       × exp((Elo_i - Elo_j) / 2000)      <- fortaleza relativa global")
    print()
    print("  P(score i-j) = Poisson(mu_h, i) × Poisson(mu_a, j) × τ(i,j)")
    print("  donde τ es la correccion Dixon-Coles para: 0-0, 1-0, 0-1, 1-1")
    print(f"{'═'*70}")

def ranking_equipos(equipos: dict, top_n: int = 48):
    """Ranking de todos los equipos segun score composite del modelo."""
    scores = []
    for nombre, e in equipos.items():
        forma = forma_score(e["forma_ultimos10"])
        # Score composite para ranking
        score = (e["elo"] * 0.40 +
                 e["xg_prom"] * 80 * 0.25 +
                 (3.0 - e["xga_prom"]) * 60 * 0.20 +
                 e["clasif_ppg"] * 50 * 0.15)
        scores.append((nombre, score, e["elo"], e["xg_prom"],
                       e["xga_prom"], e["clasif_ppg"], forma, e["grupo"]))

    scores.sort(key=lambda x: -x[1])

    print_header("RANKING PRE-TORNEO — MODELO COMPUESTO")
    print(f"\n  {'#':>3} {'Equipo':<22} {'Grp':>4} {'Score':>7} "
          f"{'Elo':>6} {'xG':>5} {'xGA':>5} {'PPG':>5} {'Forma':>6}")
    print(f"  {'-'*70}")
    for i, (n, sc, elo, xg, xga, ppg, forma, grp) in enumerate(scores[:top_n], 1):
        conf = equipos[n]["confederacion"]
        print(f"  {i:>3}  {n:<22} {grp:>3}  {sc:>7.1f} "
              f"{elo:>6} {xg:>5.2f} {xga:>5.2f} {ppg:>5.2f} {forma:>6.3f}")

# ─────────────────────────────────────────────────────────────────────────────
# EXPORTAR A CSV
# ─────────────────────────────────────────────────────────────────────────────

def export_all_groups_csv(equipos: dict, output: str = None):
    """Exporta predicciones de grupos a CSV."""
    import csv
    if output is None:
        output = str(Path(__file__).parent / "data" / "wc2026" / "predicciones_grupos.csv")

    grupos = sorted(set(e["grupo"] for e in equipos.values()))
    rows = []

    for g in grupos:
        equipos_g = {n: equipos[n] for n in equipos if equipos[n]["grupo"] == g}
        nombres = list(equipos_g.keys())
        for n1, n2 in combinations(nombres, 2):
            pred = predict_match(n1, equipos_g[n1], n2, equipos_g[n2])
            rows.append({
                "grupo": g, "equipo1": n1, "equipo2": n2,
                "goles_esp_1": pred["expected"][0],
                "goles_esp_2": pred["expected"][1],
                "marcador_prob": f"{pred['best_score'][0]}-{pred['best_score'][1]}",
                "prob_marcador_pct": round(pred["best_score_prob"] * 100, 2),
                "prob_victoria_1_pct": round(pred["p_win1"] * 100, 2),
                "prob_empate_pct": round(pred["p_draw"] * 100, 2),
                "prob_victoria_2_pct": round(pred["p_win2"] * 100, 2),
                "resultado_predicho": pred["predicted_winner"],
                "elo_1": equipos_g[n1]["elo"], "elo_2": equipos_g[n2]["elo"],
                "xg_1": equipos_g[n1]["xg_prom"], "xg_2": equipos_g[n2]["xg_prom"],
                "xga_1": equipos_g[n1]["xga_prom"], "xga_2": equipos_g[n2]["xga_prom"],
                "ppg_1": equipos_g[n1]["clasif_ppg"], "ppg_2": equipos_g[n2]["clasif_ppg"],
                "forma_1": round(forma_score(equipos_g[n1]["forma_ultimos10"]), 3),
                "forma_2": round(forma_score(equipos_g[n2]["forma_ultimos10"]), 3),
            })

    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n[OK] CSV exportado: {output}")
    print(f"     {len(rows)} partidos predichos")
    return output

# ─────────────────────────────────────────────────────────────────────────────
# VALIDACION CONTRA RESULTADOS REALES
# ─────────────────────────────────────────────────────────────────────────────

def validate_against_real(equipos: dict, resultados_reales: list[dict]):
    """
    Compara predicciones contra resultados reales ya jugados.
    resultados_reales: lista de dicts con keys t1, t2, g1_real, g2_real
    """
    print_header("VALIDACION: PREDICCION vs RESULTADO REAL")
    correctos, total = 0, 0

    for r in resultados_reales:
        t1, t2 = r["t1"], r["t2"]
        if t1 not in equipos or t2 not in equipos:
            print(f"  [AVISO] Equipo no encontrado: {t1} o {t2}")
            continue

        pred = predict_match(t1, equipos[t1], t2, equipos[t2])
        g1r, g2r = r["g1_real"], r["g2_real"]

        resultado_real = ("1" if g1r > g2r else "2" if g2r > g1r else "X")
        resultado_pred = ("1" if pred["predicted_winner"] == t1
                          else "2" if pred["predicted_winner"] == t2 else "X")

        acierto = resultado_real == resultado_pred
        if acierto:
            correctos += 1
        total += 1

        icono = "✓" if acierto else "✗"
        print(f"\n  {icono} {t1:<22} {g1r}-{g2r}  {t2}")
        print(f"    Prediccion: {pred['best_score'][0]}-{pred['best_score'][1]}"
              f"  ({pred['p_win1']*100:.1f}% / {pred['p_draw']*100:.1f}% / {pred['p_win2']*100:.1f}%)")
        print(f"    Goles esp.: {pred['expected'][0]:.2f} - {pred['expected'][1]:.2f}"
              f"  |  Elo: {equipos[t1]['elo']} vs {equipos[t2]['elo']}")

    if total > 0:
        print(f"\n{'═'*70}")
        print(f"  PRECISION RESULTADO (G/E/P): {correctos}/{total} "
              f"= {correctos/total*100:.1f}%")
        print(f"{'═'*70}")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Mundial 2026 - Predictor de Marcadores")
    parser.add_argument("--grupo", "-g", metavar="LETRA",
                        help="Predice un grupo completo (A-L)")
    parser.add_argument("--partido", "-p", nargs=2, metavar=("EQUIPO1", "EQUIPO2"),
                        help="Prediccion detallada de un partido")
    parser.add_argument("--ko", action="store_true",
                        help="Tratar como eliminatoria (con penaltis)")
    parser.add_argument("--todos", "-t", action="store_true",
                        help="Predice los 72 partidos de grupos")
    parser.add_argument("--ranking", "-r", action="store_true",
                        help="Ranking pre-torneo de los 48 equipos")
    parser.add_argument("--variables", "-v", action="store_true",
                        help="Explica variables del modelo y fuentes de datos")
    parser.add_argument("--export", "-e", action="store_true",
                        help="Exporta predicciones a CSV")
    parser.add_argument("--validar", action="store_true",
                        help="Valida modelo contra primeros resultados del Mundial")

    args = parser.parse_args()
    equipos = load_teams()

    if args.variables:
        print_variables()
        return

    if args.ranking:
        ranking_equipos(equipos)
        return

    if args.grupo:
        print_group(args.grupo.upper(), equipos)
        return

    if args.partido:
        t1_name, t2_name = args.partido[0], args.partido[1]
        # Busqueda case-insensitive
        t1_key = next((k for k in equipos if k.lower() == t1_name.lower()), None)
        t2_key = next((k for k in equipos if k.lower() == t2_name.lower()), None)
        if not t1_key or not t2_key:
            print(f"\n[ERROR] Equipo no encontrado.")
            print(f"  Equipos disponibles: {', '.join(sorted(equipos.keys()))}")
            return
        pred = predict_match(t1_key, equipos[t1_key], t2_key, equipos[t2_key])
        print_match_full(pred, equipos)
        if args.ko:
            print(f"\n  [ELIMINATORIA] {pred['ko_winner']} avanza")
            print(f"  P(penaltis {t1_key}): {pred['p_ko_win1']*100:.1f}%")
            print(f"  P(penaltis {t2_key}): {pred['p_ko_win2']*100:.1f}%")
        return

    if args.todos:
        print_all_groups(equipos)
        return

    if args.export:
        export_all_groups_csv(equipos)
        return

    if args.validar:
        # ── RESULTADOS REALES: agrega aqui los partidos ya jugados ──────────
        # Edita esta lista con los marcadores reales del Mundial 2026
        resultados_reales = [
            # Ejemplo formato: {"t1": "USA", "t2": "Panama", "g1_real": 3, "g2_real": 0}
            # Agrega aqui los resultados que ya conoces:
        ]
        if not resultados_reales:
            print("\n[INFO] Agrega los resultados reales en la seccion --validar de main.py")
            print("       Edita la lista 'resultados_reales' con los marcadores reales.")
        else:
            validate_against_real(equipos, resultados_reales)
        return

    # Sin argumentos: menu
    print_header("MUNDIAL 2026 — PREDICTOR DE MARCADORES")
    print("""
  Comandos disponibles:
  ─────────────────────────────────────────────────────────────────
  python3 predictor.py --todos              Todos los grupos (72 partidos)
  python3 predictor.py --grupo A            Grupo especifico (A hasta L)
  python3 predictor.py --partido ARG FRA    Partido especifico
  python3 predictor.py --partido ARG FRA --ko  Como eliminatoria
  python3 predictor.py --ranking            Ranking de 48 equipos
  python3 predictor.py --variables          Variables del modelo + fuentes
  python3 predictor.py --export             Exportar a CSV
  python3 predictor.py --validar            Comparar vs resultados reales
  ─────────────────────────────────────────────────────────────────
  Equipos disponibles: Argentina, France, England, Brazil, Spain,
  Portugal, Netherlands, Germany, Belgium, Croatia, Morocco,
  Colombia, Uruguay, USA, Mexico, Canada, Japan, Denmark,
  Switzerland, Senegal, Austria, Turkey, Serbia, Ukraine,
  Ecuador, Australia, Iran, Nigeria, Chile, Peru, Paraguay,
  Venezuela, Bolivia, Panama, Costa Rica, Honduras, Jamaica,
  Cameroon, South Africa, Tunisia, Ghana, New Zealand,
  Uzbekistan, South Korea, Ivory Coast, Egypt, Saudi Arabia
    """)


if __name__ == "__main__":
    main()
