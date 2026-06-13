"""
Simulador del torneo FIFA World Cup 2026.
Genera predicciones para los 104 partidos: 72 de grupos + 32 eliminatorias.
"""

import json
import warnings
import numpy as np
import pandas as pd
from pathlib import Path
from itertools import combinations
from typing import Optional

warnings.filterwarnings("ignore")

BASE_DIR = Path(__file__).resolve().parent.parent.parent
WC_DIR = BASE_DIR / "data" / "wc2026"


def load_tournament_data() -> dict:
    """Carga la estructura del torneo desde el JSON de equipos."""
    path = WC_DIR / "teams.json"
    if not path.exists():
        raise FileNotFoundError(f"No se encontro el archivo del torneo: {path}")
    with open(path) as f:
        return json.load(f)


class GroupStageSimulator:
    """Simula la fase de grupos del Mundial 2026."""

    def __init__(self, model, tournament_data: dict):
        self.model = model
        self.groups = tournament_data["groups"]
        self.team_info = tournament_data.get("team_info", {})
        self.results: dict = {}
        self.standings: dict = {}

    def generate_group_schedule(self) -> pd.DataFrame:
        """Genera el calendario completo de la fase de grupos (72 partidos)."""
        matches = []
        match_num = 1

        for group_name, group_data in self.groups.items():
            teams = group_data["teams"]
            matchday = 1

            # Pares de partidos por jornada (Round-Robin con 4 equipos = 3 jornadas)
            round_robin = list(combinations(teams, 2))
            group_matches = [
                (round_robin[0], round_robin[5]),  # Jornada 1
                (round_robin[1], round_robin[4]),  # Jornada 1
                (round_robin[2], round_robin[3]),  # Jornada 2
                (round_robin[0], round_robin[3]),  # Jornada 2
                (round_robin[1], round_robin[5]),  # Jornada 3
                (round_robin[2], round_robin[4]),  # Jornada 3
            ]

            for jornada_idx, (pair1, pair2) in enumerate(zip(
                    [round_robin[0], round_robin[1], round_robin[2]],
                    [round_robin[5], round_robin[4], round_robin[3]])):
                for home, away in [(pair1[0], pair1[1]), (pair2[0], pair2[1])]:
                    matches.append({
                        "match_id": match_num,
                        "phase": "Group Stage",
                        "group": group_name,
                        "matchday": jornada_idx + 1,
                        "home_team": home,
                        "away_team": away,
                    })
                    match_num += 1

        return pd.DataFrame(matches)

    def simulate_group(self, group_name: str) -> pd.DataFrame:
        """Simula todos los partidos de un grupo y retorna la tabla de posiciones."""
        teams = self.groups[group_name]["teams"]
        points = {t: 0 for t in teams}
        gf = {t: 0 for t in teams}
        gc = {t: 0 for t in teams}
        gd = {t: 0 for t in teams}
        wins = {t: 0 for t in teams}
        draws = {t: 0 for t in teams}
        losses = {t: 0 for t in teams}
        match_results = []

        for home, away in combinations(teams, 2):
            pred = self.model.predict_outcome(home, away, neutral=True)

            # Usar goles esperados con variacion aleatoria
            mu_h = pred["expected_home_goals"]
            mu_a = pred["expected_away_goals"]

            # Para tabla de posiciones usamos probabilidades deterministicas
            p_h = pred["home_win_prob"]
            p_d = pred["draw_prob"]

            # Marcador mas probable
            score_h = round(mu_h)
            score_a = round(mu_a)

            # Ajuste para que el marcador sea consistente con el ganador predicho
            if pred["predicted_winner"] == home and score_h <= score_a:
                score_h = score_a + 1
            elif pred["predicted_winner"] == away and score_a <= score_h:
                score_a = score_h + 1

            gf[home] += score_h
            gf[away] += score_a
            gc[home] += score_a
            gc[away] += score_h

            if score_h > score_a:
                points[home] += 3
                wins[home] += 1
                losses[away] += 1
            elif score_a > score_h:
                points[away] += 3
                wins[away] += 1
                losses[home] += 1
            else:
                points[home] += 1
                points[away] += 1
                draws[home] += 1
                draws[away] += 1

            match_results.append({
                "group": group_name,
                "home_team": home,
                "away_team": away,
                "home_goals": score_h,
                "away_goals": score_a,
                "home_win_prob": round(p_h, 3),
                "draw_prob": round(p_d, 3),
                "away_win_prob": round(pred["away_win_prob"], 3),
                "predicted_score": f"{score_h}-{score_a}",
                "result": ("H" if score_h > score_a else
                           "A" if score_a > score_h else "D"),
            })

        self.results[group_name] = match_results

        for t in teams:
            gd[t] = gf[t] - gc[t]

        standings_data = []
        for t in teams:
            standings_data.append({
                "group": group_name,
                "team": t,
                "pts": points[t],
                "w": wins[t], "d": draws[t], "l": losses[t],
                "gf": gf[t], "gc": gc[t], "gd": gd[t],
                "matches": 3,
            })

        df = pd.DataFrame(standings_data)
        df = df.sort_values(
            ["pts", "gd", "gf"], ascending=[False, False, False]
        ).reset_index(drop=True)
        df["pos"] = range(1, len(df) + 1)
        self.standings[group_name] = df
        return df

    def simulate_all_groups(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Simula todos los grupos y determina clasificados."""
        all_standings = []
        all_match_results = []

        print("\n" + "=" * 65)
        print("  FASE DE GRUPOS - PREDICCIONES")
        print("=" * 65)

        for group_name in sorted(self.groups.keys()):
            standings = self.simulate_group(group_name)
            all_standings.append(standings)
            all_match_results.extend(self.results[group_name])

            print(f"\n  GRUPO {group_name}")
            print(f"  {'POS':<4} {'EQUIPO':<25} {'PJ':>3} {'G':>3} {'E':>3} {'P':>3} "
                  f"{'GF':>4} {'GC':>4} {'DG':>4} {'PTS':>4}")
            print("  " + "-" * 60)
            for _, row in standings.iterrows():
                qual = "*" if row["pos"] <= 2 else " "
                print(f"  {qual}{row['pos']:<3} {row['team']:<25} {row['matches']:>3} "
                      f"{row['w']:>3} {row['d']:>3} {row['l']:>3} "
                      f"{row['gf']:>4} {row['gc']:>4} {row['gd']:>4} {row['pts']:>4}")

        print("\n  * = Clasificado directo (top 2 por grupo)")

        standings_df = pd.concat(all_standings, ignore_index=True)
        matches_df = pd.DataFrame(all_match_results)
        return standings_df, matches_df

    def get_qualified_teams(self, standings_df: pd.DataFrame) -> list[str]:
        """
        Determina los 32 clasificados:
        - Top 2 de cada grupo (24 equipos)
        - 8 mejores terceros
        """
        # Top 2 por grupo
        top2 = standings_df[standings_df["pos"] <= 2]["team"].tolist()

        # Terceros clasificados
        thirds = standings_df[standings_df["pos"] == 3].sort_values(
            ["pts", "gd", "gf"], ascending=[False, False, False]
        ).head(8)["team"].tolist()

        qualified = top2 + thirds

        print(f"\n[CLASIFICADOS] {len(qualified)} equipos avanzan a eliminatorias:")
        print(f"  Top 2 de grupos: {len(top2)}")
        print(f"  Mejores terceros: {len(thirds)}")
        return qualified


class KnockoutSimulator:
    """Simula las rondas eliminatorias (Round of 32 al Final)."""

    ROUNDS = [
        ("Round of 32", 16),
        ("Round of 16", 8),
        ("Quarterfinals", 4),
        ("Semifinals", 2),
        ("Third Place", 1),
        ("Final", 1),
    ]

    def __init__(self, model, qualified_teams: list):
        self.model = model
        self.bracket = qualified_teams
        self.results: list = []

    def simulate_round(self, teams: list, round_name: str) -> tuple[list, list]:
        """Simula una ronda eliminatoria. Retorna (ganadores, resultados)."""
        winners = []
        match_results = []

        print(f"\n  {round_name.upper()}")
        print("  " + "-" * 60)

        for i in range(0, len(teams), 2):
            if i + 1 >= len(teams):
                winners.append(teams[i])
                continue

            t1, t2 = teams[i], teams[i + 1]
            pred = self.model.predict_knockout(t1, t2)

            winner = pred["most_likely_winner"]
            loser = t2 if winner == t1 else t1

            t1_prob = pred["team1_win_prob"]
            t2_prob = pred["team2_win_prob"]

            print(f"  {t1:<22} vs {t2:<22} -> "
                  f"{winner} ({max(t1_prob, t2_prob)*100:.1f}%)")

            match_results.append({
                "phase": round_name,
                "team1": t1,
                "team2": t2,
                "predicted_winner": winner,
                "predicted_loser": loser,
                "team1_win_prob": round(t1_prob, 4),
                "team2_win_prob": round(t2_prob, 4),
                "predicted_score": pred["expected_score"],
            })

            winners.append(winner)
            self.results.append(match_results[-1])

        return winners, match_results

    def simulate_knockout_stage(self, standings_df: pd.DataFrame,
                                 groups: dict) -> pd.DataFrame:
        """Simula todas las rondas eliminatorias."""
        print("\n" + "=" * 65)
        print("  RONDAS ELIMINATORIAS - PREDICCIONES")
        print("=" * 65)

        # Construccion del bracket segun posiciones de grupo
        bracket = self._build_bracket(standings_df, groups)

        # Round of 32 -> Round of 16 -> QF -> SF
        current_teams = bracket
        all_matches = []

        for round_name, n_matches in self.ROUNDS[:4]:
            if len(current_teams) < 2:
                break
            current_teams, matches = self.simulate_round(current_teams, round_name)
            all_matches.extend(matches)

        # Tercer puesto y Final con los 4 semifinalistas
        if len(self.results) >= 2:
            semi_results = [r for r in self.results if r["phase"] == "Semifinals"]
            if len(semi_results) >= 2:
                finalists = [semi_results[0]["predicted_winner"],
                             semi_results[1]["predicted_winner"]]
                third_place = [semi_results[0]["predicted_loser"],
                               semi_results[1]["predicted_loser"]]

                print(f"\n  TERCER LUGAR")
                print("  " + "-" * 60)
                _, t3_matches = self.simulate_round(third_place, "Third Place")
                all_matches.extend(t3_matches)

                print(f"\n  FINAL")
                print("  " + "-" * 60)
                _, final_matches = self.simulate_round(finalists, "Final")
                all_matches.extend(final_matches)

                final = final_matches[0]
                print(f"\n  CAMPEON PREDICHO: {final['predicted_winner'].upper()}")
                print(f"  Probabilidad: {max(final['team1_win_prob'], final['team2_win_prob'])*100:.1f}%")

        return pd.DataFrame(all_matches)

    def _build_bracket(self, standings_df: pd.DataFrame, groups: dict) -> list:
        """
        Construye el bracket de 32 equipos segun el formato oficial WC2026.
        Formato: 1A vs mejor3(B/C/D), 2A vs mejor3(E/F/G), etc.
        Se usa emparejamiento simplificado por posicion de grupo.
        """
        winners, runners_up, thirds = [], [], []

        for g in sorted(groups.keys()):
            g_df = standings_df[standings_df["group"] == g].sort_values("pos")
            if len(g_df) >= 1:
                winners.append(g_df.iloc[0]["team"])
            if len(g_df) >= 2:
                runners_up.append(g_df.iloc[1]["team"])
            if len(g_df) >= 3:
                thirds.append(g_df.iloc[2]["team"])

        # Mejores 8 terceros
        thirds_df = standings_df[standings_df["pos"] == 3].sort_values(
            ["pts", "gd", "gf"], ascending=[False, False, False]
        ).head(8)
        best8_thirds = thirds_df["team"].tolist()

        # Bracket: alternar ganadores y subcampeones para cruces equilibrados
        bracket = []
        for i in range(len(winners)):
            bracket.append(winners[i])
            if i < len(runners_up):
                bracket.append(runners_up[i])

        bracket.extend(best8_thirds)
        return bracket[:32]


class TournamentPredictor:
    """Orquestador principal: ejecuta prediccion completa del Mundial 2026."""

    def __init__(self, model):
        self.model = model
        self.tournament_data = load_tournament_data()
        self.group_sim = GroupStageSimulator(model, self.tournament_data)
        self.all_predictions: dict = {}

    def run_full_prediction(self) -> dict:
        """Ejecuta prediccion completa de los 104 partidos."""
        print("\n" + "=" * 65)
        print("  FIFA WORLD CUP 2026 - PREDICCION COMPLETA")
        print("  Modelo: Dixon-Coles con correccion de baja puntuacion")
        print("=" * 65)

        # Fase de grupos
        standings_df, group_matches_df = self.group_sim.simulate_all_groups()

        # Equipos clasificados
        qualified = self.group_sim.get_qualified_teams(standings_df)

        # Eliminatorias
        knockout_sim = KnockoutSimulator(self.model, qualified)
        knockout_df = knockout_sim.simulate_knockout_stage(
            standings_df, self.tournament_data["groups"]
        )

        self.all_predictions = {
            "standings": standings_df,
            "group_matches": group_matches_df,
            "knockout_matches": knockout_df,
            "qualified_teams": qualified,
            "champion": (
                knockout_df[knockout_df["phase"] == "Final"]["predicted_winner"].iloc[0]
                if "Final" in knockout_df["phase"].values else "TBD"
            ),
        }

        self._print_summary()
        return self.all_predictions

    def _print_summary(self):
        pred = self.all_predictions
        total_matches = len(pred["group_matches"]) + len(pred["knockout_matches"])
        champion = pred.get("champion", "TBD")

        print("\n" + "=" * 65)
        print("  RESUMEN DE PREDICCIONES")
        print("=" * 65)
        print(f"  Partidos fase de grupos    : {len(pred['group_matches'])}")
        print(f"  Partidos eliminatorias     : {len(pred['knockout_matches'])}")
        print(f"  Total partidos predichos   : {total_matches}")
        print(f"  CAMPEON PREDICHO           : {champion.upper()}")
        print("=" * 65)

    def export_predictions(self, output_path: str = None) -> str:
        """Exporta todas las predicciones a un archivo Excel."""
        if not self.all_predictions:
            raise RuntimeError("Ejecute run_full_prediction() primero.")

        if output_path is None:
            output_path = str(BASE_DIR / "data" / "wc2026" / "predicciones_wc2026.xlsx")

        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            # Fase de grupos
            self.all_predictions["group_matches"].to_excel(
                writer, sheet_name="Fase de Grupos", index=False
            )
            # Tabla de posiciones
            self.all_predictions["standings"].to_excel(
                writer, sheet_name="Posiciones", index=False
            )
            # Eliminatorias
            self.all_predictions["knockout_matches"].to_excel(
                writer, sheet_name="Eliminatorias", index=False
            )
            # Clasificados
            pd.DataFrame(
                {"equipo": self.all_predictions["qualified_teams"]}
            ).to_excel(writer, sheet_name="Clasificados", index=False)

        print(f"\n[OK] Predicciones exportadas: {output_path}")
        return output_path

    def predict_single_match(self, team1: str, team2: str,
                              knockout: bool = False) -> None:
        """Imprime prediccion detallada para un partido especifico."""
        print(f"\n{'='*65}")
        print(f"  {team1.upper()} vs {team2.upper()}")
        print(f"  Tipo: {'Eliminatoria (penaltis posibles)' if knockout else 'Fase de grupos'}")
        print(f"{'='*65}")

        if knockout:
            pred = self.model.predict_knockout(team1, team2)
            print(f"\n  Prob. victoria {team1:25}: {pred['team1_win_prob']*100:.1f}%")
            print(f"  Prob. victoria {team2:25}: {pred['team2_win_prob']*100:.1f}%")
            print(f"\n  Marcador esperado: {pred['expected_score']}")
            print(f"  GANADOR PREDICHO: {pred['most_likely_winner'].upper()}")
        else:
            pred = self.model.predict_outcome(team1, team2, neutral=True)
            print(f"\n  Prob. victoria {team1:25}: {pred['home_win_prob']*100:.1f}%")
            print(f"  Prob. empate                           : {pred['draw_prob']*100:.1f}%")
            print(f"  Prob. victoria {team2:25}: {pred['away_win_prob']*100:.1f}%")
            print(f"\n  Goles esperados: {pred['expected_home_goals']:.2f} - {pred['expected_away_goals']:.2f}")
            print(f"  Marcador mas probable: {pred['most_likely_score']} "
                  f"({pred['most_likely_score_prob']*100:.1f}%)")
            print(f"  RESULTADO PREDICHO: {pred['predicted_winner'].upper()}")

        # Top 5 marcadores mas probables
        scores_df = self.model.get_score_probabilities_table(team1, team2, max_goals=5)
        print(f"\n  TOP 5 MARCADORES MAS PROBABLES:")
        print(f"  {'MARCADOR':>10} {'PROBABILIDAD':>14}")
        print("  " + "-" * 28)
        for _, row in scores_df.head(5).iterrows():
            print(f"  {team1[:10]}:{row['home_goals']} - {team2[:10]}:{row['away_goals']}"
                  f"  {row['pct']:>10}")
        print()
