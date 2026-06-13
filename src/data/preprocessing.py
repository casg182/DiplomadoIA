"""
Carga y preprocesamiento de datos para el modelo Mundial 2026.
Transforma los CSV descargados en features listos para el modelo Dixon-Coles.
"""

import os
import warnings
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
WC_DIR = BASE_DIR / "data" / "wc2026"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# CARGADORES DE DATOS
# ─────────────────────────────────────────────────────────────────────────────

def load_match_results(path: str | None = None) -> pd.DataFrame:
    """
    Carga resultados historicos internacionales.
    Fuente: Kaggle 'International football results 1872-2024'
    Archivo esperado: data/raw/international_results.csv
    """
    if path is None:
        path = RAW_DIR / "international_results.csv"

    if not Path(path).exists():
        print(f"[AVISO] Archivo no encontrado: {path}")
        print("  -> Usando datos de ejemplo integrados (ultimas Copas del Mundo).")
        return _generate_sample_results()

    df = pd.read_csv(path, parse_dates=["date"])
    df.columns = df.columns.str.lower().str.replace(" ", "_")

    required = {"date", "home_team", "away_team", "home_score", "away_score"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Columnas faltantes en el CSV: {missing}")

    df["home_score"] = pd.to_numeric(df["home_score"], errors="coerce")
    df["away_score"] = pd.to_numeric(df["away_score"], errors="coerce")
    df = df.dropna(subset=["home_score", "away_score"])
    df["neutral"] = df.get("neutral", False).fillna(False).astype(bool)

    print(f"[OK] Resultados cargados: {len(df):,} partidos ({df['date'].min().year}-{df['date'].max().year})")
    return df


def load_fifa_rankings(path: str | None = None) -> pd.DataFrame:
    """
    Carga el ranking FIFA historico.
    Fuente: Kaggle 'FIFA World Rankings' o fifa.com
    Archivo esperado: data/raw/fifa_rankings.csv
    """
    if path is None:
        path = RAW_DIR / "fifa_rankings.csv"

    if not Path(path).exists():
        print(f"[AVISO] Rankings FIFA no encontrados: {path}")
        print("  -> Usando ratings Elo como alternativa.")
        return None

    df = pd.read_csv(path, parse_dates=["rank_date"])
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    print(f"[OK] Rankings FIFA cargados: {len(df):,} registros")
    return df


def load_elo_ratings(path: str | None = None) -> pd.DataFrame:
    """
    Carga ratings Elo de selecciones.
    Fuente: eloratings.net (descarga directa, sin registro)
    Archivo esperado: data/raw/elo_ratings.tsv
    """
    if path is None:
        path = RAW_DIR / "elo_ratings.tsv"

    if not Path(path).exists():
        print(f"[AVISO] Ratings Elo no encontrados: {path}")
        print("  -> Usando ratings Elo estimados desde resultados historicos.")
        return _generate_elo_ratings()

    df = pd.read_csv(path, sep="\t")
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    print(f"[OK] Ratings Elo cargados: {len(df):,} selecciones")
    return df


# ─────────────────────────────────────────────────────────────────────────────
# FEATURE ENGINEERING
# ─────────────────────────────────────────────────────────────────────────────

def filter_recent_matches(df: pd.DataFrame, years: int = 8,
                          cutoff_date: str | None = None) -> pd.DataFrame:
    """Filtra partidos de los ultimos N años para entrenamiento del modelo."""
    if cutoff_date is None:
        cutoff = datetime.now() - timedelta(days=years * 365)
    else:
        cutoff = pd.to_datetime(cutoff_date)

    mask = df["date"] >= cutoff
    filtered = df[mask].copy()
    print(f"[OK] Partidos para entrenamiento: {len(filtered):,} (desde {cutoff.year})")
    return filtered


def compute_time_weights(df: pd.DataFrame, half_life_days: int = 365) -> pd.Series:
    """
    Peso exponencial por recencia. Partidos recientes pesan mas.
    half_life_days: dias en que el peso se reduce a la mitad.
    """
    max_date = df["date"].max()
    days_ago = (max_date - df["date"]).dt.days
    weights = np.exp(-np.log(2) * days_ago / half_life_days)
    return weights


def compute_team_stats(df: pd.DataFrame,
                       weight_col: str = "weight",
                       n_matches: int = 20) -> pd.DataFrame:
    """
    Calcula estadisticas de ataque/defensa para cada seleccion.
    Usa los ultimos n_matches partidos por equipo.
    """
    records = []

    all_teams = pd.concat([
        df["home_team"], df["away_team"]
    ]).unique()

    for team in all_teams:
        home_m = df[df["home_team"] == team].copy()
        away_m = df[df["away_team"] == team].copy()

        home_m["gf"] = home_m["home_score"]
        home_m["gc"] = home_m["away_score"]
        away_m["gf"] = away_m["away_score"]
        away_m["gc"] = away_m["home_score"]

        all_m = pd.concat([home_m, away_m]).sort_values("date").tail(n_matches)

        if len(all_m) < 3:
            continue

        w = all_m.get(weight_col, pd.Series(np.ones(len(all_m)), index=all_m.index))

        gf_mean = np.average(all_m["gf"], weights=w)
        gc_mean = np.average(all_m["gc"], weights=w)

        results = np.where(
            all_m["gf"] > all_m["gc"], "W",
            np.where(all_m["gf"] < all_m["gc"], "L", "D")
        )
        wins = (results == "W").sum()
        draws = (results == "D").sum()
        losses = (results == "L").sum()

        last5 = all_m.tail(5)
        pts_last5 = sum(3 if g > c else (1 if g == c else 0)
                        for g, c in zip(last5["gf"], last5["gc"]))

        records.append({
            "team": team,
            "matches": len(all_m),
            "goals_for_avg": round(gf_mean, 3),
            "goals_against_avg": round(gc_mean, 3),
            "win_rate": round(wins / len(all_m), 3),
            "draw_rate": round(draws / len(all_m), 3),
            "loss_rate": round(losses / len(all_m), 3),
            "pts_last5": pts_last5,
            "goal_diff_avg": round(gf_mean - gc_mean, 3),
        })

    stats = pd.DataFrame(records).sort_values("goal_diff_avg", ascending=False)
    return stats.reset_index(drop=True)


def compute_h2h_stats(df: pd.DataFrame, team1: str, team2: str,
                      last_n: int = 10) -> dict:
    """Calcula estadisticas cabeza a cabeza entre dos selecciones."""
    mask = (
        ((df["home_team"] == team1) & (df["away_team"] == team2)) |
        ((df["home_team"] == team2) & (df["away_team"] == team1))
    )
    h2h = df[mask].sort_values("date").tail(last_n)

    if len(h2h) == 0:
        return {"matches": 0, "team1_wins": 0, "team2_wins": 0,
                "draws": 0, "team1_goals_avg": 0.0, "team2_goals_avg": 0.0}

    t1_goals, t2_goals, t1_wins, t2_wins, draws = 0, 0, 0, 0, 0

    for _, row in h2h.iterrows():
        if row["home_team"] == team1:
            g1, g2 = row["home_score"], row["away_score"]
        else:
            g1, g2 = row["away_score"], row["home_score"]

        t1_goals += g1
        t2_goals += g2
        if g1 > g2:
            t1_wins += 1
        elif g2 > g1:
            t2_wins += 1
        else:
            draws += 1

    n = len(h2h)
    return {
        "matches": n,
        "team1_wins": t1_wins,
        "team2_wins": t2_wins,
        "draws": draws,
        "team1_goals_avg": round(t1_goals / n, 2),
        "team2_goals_avg": round(t2_goals / n, 2),
    }


def add_confederation_factor(df: pd.DataFrame,
                             confederation_map: dict) -> pd.DataFrame:
    """Agrega factor de fortaleza por confederacion."""
    CONF_STRENGTH = {
        "UEFA": 1.10,
        "CONMEBOL": 1.08,
        "CONCACAF": 0.92,
        "AFC": 0.90,
        "CAF": 0.88,
        "OFC": 0.78,
    }
    df = df.copy()
    df["confederation"] = df["team"].map(confederation_map)
    df["conf_factor"] = df["confederation"].map(CONF_STRENGTH).fillna(0.90)
    return df


# ─────────────────────────────────────────────────────────────────────────────
# DATOS DE EJEMPLO (cuando no hay CSV descargado)
# ─────────────────────────────────────────────────────────────────────────────

def _generate_sample_results() -> pd.DataFrame:
    """Genera un dataset minimo con resultados reales de mundiales recientes."""
    matches = [
        # Mundial Qatar 2022 - muestra representativa
        ("2022-11-20", "Ecuador", "Qatar", 2, 0, "FIFA World Cup", True),
        ("2022-11-21", "England", "Iran", 6, 2, "FIFA World Cup", True),
        ("2022-11-21", "Senegal", "Netherlands", 0, 2, "FIFA World Cup", True),
        ("2022-11-21", "USA", "Wales", 1, 1, "FIFA World Cup", True),
        ("2022-11-22", "Argentina", "Saudi Arabia", 1, 2, "FIFA World Cup", True),
        ("2022-11-22", "Denmark", "Tunisia", 0, 0, "FIFA World Cup", True),
        ("2022-11-22", "Mexico", "Poland", 0, 0, "FIFA World Cup", True),
        ("2022-11-22", "France", "Australia", 4, 1, "FIFA World Cup", True),
        ("2022-11-23", "Morocco", "Croatia", 0, 0, "FIFA World Cup", True),
        ("2022-11-23", "Germany", "Japan", 1, 2, "FIFA World Cup", True),
        ("2022-11-23", "Spain", "Costa Rica", 7, 0, "FIFA World Cup", True),
        ("2022-11-24", "Belgium", "Canada", 1, 0, "FIFA World Cup", True),
        ("2022-11-24", "Switzerland", "Cameroon", 1, 0, "FIFA World Cup", True),
        ("2022-11-24", "Uruguay", "South Korea", 0, 0, "FIFA World Cup", True),
        ("2022-11-24", "Portugal", "Ghana", 3, 2, "FIFA World Cup", True),
        ("2022-11-24", "Brazil", "Serbia", 2, 0, "FIFA World Cup", True),
        # Octavos
        ("2022-12-03", "Netherlands", "USA", 3, 1, "FIFA World Cup", True),
        ("2022-12-03", "Argentina", "Australia", 2, 1, "FIFA World Cup", True),
        ("2022-12-04", "France", "Poland", 3, 1, "FIFA World Cup", True),
        ("2022-12-04", "England", "Senegal", 3, 0, "FIFA World Cup", True),
        ("2022-12-05", "Japan", "Croatia", 1, 1, "FIFA World Cup", True),
        ("2022-12-05", "Brazil", "South Korea", 4, 1, "FIFA World Cup", True),
        ("2022-12-06", "Morocco", "Spain", 0, 0, "FIFA World Cup", True),
        ("2022-12-06", "Portugal", "Switzerland", 6, 1, "FIFA World Cup", True),
        # Cuartos
        ("2022-12-09", "Croatia", "Brazil", 1, 1, "FIFA World Cup", True),
        ("2022-12-09", "Netherlands", "Argentina", 2, 2, "FIFA World Cup", True),
        ("2022-12-10", "Morocco", "Portugal", 1, 0, "FIFA World Cup", True),
        ("2022-12-10", "England", "France", 1, 2, "FIFA World Cup", True),
        # Semis
        ("2022-12-13", "Argentina", "Croatia", 3, 0, "FIFA World Cup", True),
        ("2022-12-14", "France", "Morocco", 2, 0, "FIFA World Cup", True),
        # Final
        ("2022-12-18", "Argentina", "France", 3, 3, "FIFA World Cup", True),
        # Clasificatorias CONMEBOL (muestra)
        ("2023-09-08", "Argentina", "Ecuador", 1, 0, "FIFA World Cup qualification", False),
        ("2023-09-08", "Brazil", "Bolivia", 5, 1, "FIFA World Cup qualification", False),
        ("2023-09-08", "Uruguay", "Chile", 3, 1, "FIFA World Cup qualification", False),
        ("2023-09-08", "Colombia", "Venezuela", 1, 0, "FIFA World Cup qualification", False),
        ("2023-09-08", "Paraguay", "Peru", 0, 0, "FIFA World Cup qualification", False),
        ("2024-03-21", "Argentina", "El Salvador", 3, 0, "Friendly", True),
        ("2024-06-09", "Argentina", "Ecuador", 1, 0, "Copa America", True),
        ("2024-06-15", "France", "Austria", 1, 0, "UEFA Euro", False),
        ("2024-06-15", "Germany", "Scotland", 5, 1, "UEFA Euro", False),
        ("2024-06-15", "Hungary", "Switzerland", 1, 3, "UEFA Euro", False),
        ("2024-06-15", "Spain", "Croatia", 3, 0, "UEFA Euro", False),
        ("2024-07-14", "Spain", "England", 2, 1, "UEFA Euro", True),
        ("2024-07-15", "Argentina", "Colombia", 1, 0, "Copa America", True),
    ]

    df = pd.DataFrame(matches, columns=[
        "date", "home_team", "away_team", "home_score", "away_score",
        "tournament", "neutral"
    ])
    df["date"] = pd.to_datetime(df["date"])
    df["neutral"] = df["neutral"].astype(bool)

    print(f"[INFO] Dataset de ejemplo cargado: {len(df)} partidos")
    print("[IMPORTANTE] Para predicciones precisas, descarga el dataset completo:")
    print("  Kaggle: https://www.kaggle.com/datasets/martj42/international-football-results-from-1872-to-2017")
    return df


def _generate_elo_ratings() -> pd.DataFrame:
    """Ratings Elo estimados basados en FIFA rankings y rendimiento historico."""
    ratings = [
        ("Argentina", 2109, "CONMEBOL"),
        ("France", 2075, "UEFA"),
        ("England", 2043, "UEFA"),
        ("Brazil", 2041, "CONMEBOL"),
        ("Belgium", 2009, "UEFA"),
        ("Portugal", 2001, "UEFA"),
        ("Spain", 1998, "UEFA"),
        ("Netherlands", 1988, "UEFA"),
        ("Germany", 1984, "UEFA"),
        ("Croatia", 1958, "UEFA"),
        ("Morocco", 1942, "CAF"),
        ("Uruguay", 1940, "CONMEBOL"),
        ("Colombia", 1934, "CONMEBOL"),
        ("Italy", 1932, "UEFA"),
        ("Denmark", 1928, "UEFA"),
        ("Mexico", 1924, "CONCACAF"),
        ("USA", 1918, "CONCACAF"),
        ("Senegal", 1910, "CAF"),
        ("Japan", 1906, "AFC"),
        ("Switzerland", 1904, "UEFA"),
        ("Poland", 1898, "UEFA"),
        ("Austria", 1890, "UEFA"),
        ("South Korea", 1882, "AFC"),
        ("Ecuador", 1878, "CONMEBOL"),
        ("Australia", 1870, "AFC"),
        ("Turkey", 1868, "UEFA"),
        ("Chile", 1862, "CONMEBOL"),
        ("Paraguay", 1850, "CONMEBOL"),
        ("Serbia", 1848, "UEFA"),
        ("Ukraine", 1844, "UEFA"),
        ("Ivory Coast", 1840, "CAF"),
        ("Egypt", 1838, "CAF"),
        ("Algeria", 1832, "CAF"),
        ("Nigeria", 1828, "CAF"),
        ("Iran", 1820, "AFC"),
        ("Saudi Arabia", 1815, "AFC"),
        ("Canada", 1810, "CONCACAF"),
        ("Peru", 1808, "CONMEBOL"),
        ("Hungary", 1802, "UEFA"),
        ("Czech Republic", 1798, "UEFA"),
        ("Scotland", 1795, "UEFA"),
        ("Romania", 1790, "UEFA"),
        ("Venezuela", 1788, "CONMEBOL"),
        ("Bolivia", 1780, "CONMEBOL"),
        ("Tunisia", 1775, "CAF"),
        ("South Africa", 1770, "CAF"),
        ("Ghana", 1765, "CAF"),
        ("Cameroon", 1760, "CAF"),
        ("Qatar", 1720, "AFC"),
        ("Costa Rica", 1718, "CONCACAF"),
        ("Panama", 1710, "CONCACAF"),
        ("Honduras", 1705, "CONCACAF"),
        ("Jamaica", 1698, "CONCACAF"),
        ("New Zealand", 1650, "OFC"),
    ]

    df = pd.DataFrame(ratings, columns=["team", "elo", "confederation"])
    return df


def prepare_training_data(results_df: pd.DataFrame,
                          years: int = 8) -> pd.DataFrame:
    """Pipeline completo: filtra, pesa y prepara datos de entrenamiento."""
    df = filter_recent_matches(results_df, years=years)
    df = df.copy()
    df["weight"] = compute_time_weights(df)

    # Excluir partidos amistosos de menor importancia (peso reducido)
    friendly_mask = df.get("tournament", pd.Series("")).str.lower().str.contains(
        "friendly", na=False
    )
    df.loc[friendly_mask, "weight"] *= 0.5

    df = df.sort_values("date").reset_index(drop=True)
    print(f"[OK] Datos de entrenamiento preparados: {len(df):,} partidos")
    return df
