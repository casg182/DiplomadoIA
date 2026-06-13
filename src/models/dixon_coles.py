"""
Modelo Dixon-Coles para prediccion de resultados de futbol.

Referencia: Dixon, M.J. & Coles, S.G. (1997). "Modelling Association Football
Scores and Inefficiencies in the Football Betting Market". Applied Statistics.

El modelo estima parametros de ataque/defensa por equipo y predice
la distribucion de probabilidad sobre todos los posibles marcadores.
Correccion de Dixon-Coles para resultados de baja puntuacion (0-0, 1-0, 0-1, 1-1).
"""

import warnings
import numpy as np
import pandas as pd
from scipy.stats import poisson
from scipy.optimize import minimize
from typing import Tuple

warnings.filterwarnings("ignore")


class DixonColesModel:
    """
    Modelo de Poisson bivariante con corrección Dixon-Coles.

    Parámetros estimados por equipo:
      - attack[team]  : fuerza ofensiva (mayor = más goles)
      - defense[team] : fuerza defensiva (menor = menos concede)

    Parámetros globales:
      - home_advantage : bonificación por jugar en casa (neutral=0 en mundial)
      - rho            : corrección para marcadores bajos
    """

    def __init__(self):
        self.attack_params: dict = {}
        self.defense_params: dict = {}
        self.home_advantage: float = 0.0
        self.rho: float = 0.0
        self.teams: list = []
        self._is_fitted: bool = False

    # ─────────────────────────────────────────────────────────────────────────
    # ENTRENAMIENTO
    # ─────────────────────────────────────────────────────────────────────────

    def fit(self, df: pd.DataFrame, weight_col: str = "weight") -> "DixonColesModel":
        """
        Ajusta el modelo con los datos historicos.

        Args:
            df: DataFrame con columnas home_team, away_team,
                home_score, away_score, weight (opcional)
            weight_col: columna de pesos por recencia
        """
        self.teams = sorted(set(df["home_team"]) | set(df["away_team"]))
        n_teams = len(self.teams)
        team_idx = {t: i for i, t in enumerate(self.teams)}

        weights = df[weight_col].values if weight_col in df.columns else np.ones(len(df))

        home_scores = df["home_score"].values.astype(int)
        away_scores = df["away_score"].values.astype(int)
        home_idx = df["home_team"].map(team_idx).values
        away_idx = df["away_team"].map(team_idx).values
        neutral = df.get("neutral", pd.Series(False, index=df.index)).values.astype(bool)

        # Parametros iniciales: ataque=1.0, defensa=1.0, ventaja local=0.3, rho=-0.1
        x0 = np.concatenate([
            np.ones(n_teams),        # attack
            np.ones(n_teams),        # defense
            [0.3],                   # home_advantage (log scale)
            [-0.1],                  # rho
        ])

        def neg_log_likelihood(params):
            attack = np.exp(params[:n_teams])
            defense = np.exp(params[n_teams:2 * n_teams])
            home_adv = np.exp(params[-2])
            rho = params[-1]

            # Restriccion: media de ataque = 1 (identificabilidad)
            attack = attack / attack.mean()

            log_lik = 0.0
            for i in range(len(df)):
                ha = home_idx[i]
                aa = away_idx[i]
                home_h = 1.0 if not neutral[i] else 1.0  # neutral en Mundial
                mu_h = attack[ha] * defense[aa] * home_adv * home_h
                mu_a = attack[aa] * defense[ha]

                hg = home_scores[i]
                ag = away_scores[i]

                log_p_h = poisson.logpmf(hg, mu_h)
                log_p_a = poisson.logpmf(ag, mu_a)

                # Corrección Dixon-Coles para marcadores bajos
                if hg == 0 and ag == 0:
                    corr = np.log(max(1 - mu_h * mu_a * rho, 1e-10))
                elif hg == 1 and ag == 0:
                    corr = np.log(max(1 + mu_a * rho, 1e-10))
                elif hg == 0 and ag == 1:
                    corr = np.log(max(1 + mu_h * rho, 1e-10))
                elif hg == 1 and ag == 1:
                    corr = np.log(max(1 - rho, 1e-10))
                else:
                    corr = 0.0

                log_lik += weights[i] * (log_p_h + log_p_a + corr)

            return -log_lik

        print("[DC] Ajustando modelo Dixon-Coles...")
        result = minimize(
            neg_log_likelihood,
            x0,
            method="L-BFGS-B",
            options={"maxiter": 500, "ftol": 1e-9},
        )

        if not result.success:
            print(f"[AVISO] Optimizacion no convergio: {result.message}")

        params = result.x
        attack_raw = np.exp(params[:n_teams])
        defense_raw = np.exp(params[n_teams:2 * n_teams])
        attack_norm = attack_raw / attack_raw.mean()

        self.attack_params = dict(zip(self.teams, attack_norm))
        self.defense_params = dict(zip(self.teams, defense_raw))
        self.home_advantage = float(np.exp(params[-2]))
        self.rho = float(params[-1])
        self._is_fitted = True

        print(f"[DC] Modelo ajustado. Equipos: {n_teams}. "
              f"Ventaja local: {self.home_advantage:.3f}. Rho: {self.rho:.4f}")
        return self

    # ─────────────────────────────────────────────────────────────────────────
    # PREDICCION
    # ─────────────────────────────────────────────────────────────────────────

    def predict_score_matrix(self, home_team: str, away_team: str,
                             neutral: bool = True,
                             max_goals: int = 8) -> np.ndarray:
        """
        Calcula la matriz de probabilidades para todos los marcadores posibles.

        Returns:
            ndarray de shape (max_goals+1, max_goals+1) donde [i,j] =
            P(home_goals=i, away_goals=j)
        """
        if not self._is_fitted:
            raise RuntimeError("El modelo no ha sido ajustado. Llame a .fit() primero.")

        att_h = self._get_attack(home_team)
        def_h = self._get_defense(home_team)
        att_a = self._get_attack(away_team)
        def_a = self._get_defense(away_team)

        home_factor = 1.0 if neutral else self.home_advantage
        mu_h = att_h * def_a * home_factor
        mu_a = att_a * def_h

        matrix = np.zeros((max_goals + 1, max_goals + 1))

        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                p = poisson.pmf(i, mu_h) * poisson.pmf(j, mu_a)

                # Corrección Dixon-Coles
                if i == 0 and j == 0:
                    p *= max(1 - mu_h * mu_a * self.rho, 1e-10)
                elif i == 1 and j == 0:
                    p *= max(1 + mu_a * self.rho, 1e-10)
                elif i == 0 and j == 1:
                    p *= max(1 + mu_h * self.rho, 1e-10)
                elif i == 1 and j == 1:
                    p *= max(1 - self.rho, 1e-10)

                matrix[i, j] = max(p, 0.0)

        # Renormalizar
        total = matrix.sum()
        if total > 0:
            matrix /= total

        return matrix

    def predict_outcome(self, home_team: str, away_team: str,
                        neutral: bool = True) -> dict:
        """
        Predice probabilidades de victoria/empate/derrota y marcador mas probable.

        Returns:
            dict con home_win, draw, away_win, expected_home, expected_away,
            most_likely_score, score_probability
        """
        matrix = self.predict_score_matrix(home_team, away_team, neutral)

        p_home_win = float(np.tril(matrix, -1).sum())  # home > away (lower triangle)
        p_draw = float(np.trace(matrix))
        p_away_win = float(np.triu(matrix, 1).sum())   # away > home (upper triangle)

        # Marcador mas probable
        max_idx = np.unravel_index(np.argmax(matrix), matrix.shape)
        most_likely = (int(max_idx[0]), int(max_idx[1]))

        max_goals = matrix.shape[0] - 1
        goals_range = np.arange(max_goals + 1)
        exp_home = float(np.sum(matrix.sum(axis=1) * goals_range))
        exp_away = float(np.sum(matrix.sum(axis=0) * goals_range))

        return {
            "home_team": home_team,
            "away_team": away_team,
            "home_win_prob": round(p_home_win, 4),
            "draw_prob": round(p_draw, 4),
            "away_win_prob": round(p_away_win, 4),
            "expected_home_goals": round(exp_home, 2),
            "expected_away_goals": round(exp_away, 2),
            "most_likely_score": f"{most_likely[0]}-{most_likely[1]}",
            "most_likely_score_prob": round(float(matrix[most_likely]), 4),
            "predicted_winner": (
                home_team if p_home_win > p_away_win and p_home_win > p_draw
                else (away_team if p_away_win > p_home_win and p_away_win > p_draw
                      else "Draw")
            ),
        }

    def predict_knockout(self, team1: str, team2: str) -> dict:
        """
        Predice probabilidades en eliminatoria (sin empate, incluye penaltis).
        """
        pred = self.predict_outcome(team1, team2, neutral=True)
        draw_p = pred["draw_prob"]

        # En penaltis se asume 50/50 ajustado por fortaleza relativa
        elo_factor = self._elo_strength_ratio(team1, team2)
        penalties_team1 = 0.5 * elo_factor
        penalties_team2 = 1.0 - penalties_team1

        p1_win = pred["home_win_prob"] + draw_p * penalties_team1
        p2_win = pred["away_win_prob"] + draw_p * penalties_team2

        return {
            "team1": team1,
            "team2": team2,
            "team1_win_prob": round(p1_win, 4),
            "team2_win_prob": round(p2_win, 4),
            "expected_score": pred["most_likely_score"],
            "most_likely_winner": team1 if p1_win > p2_win else team2,
        }

    # ─────────────────────────────────────────────────────────────────────────
    # UTILIDADES
    # ─────────────────────────────────────────────────────────────────────────

    def _get_attack(self, team: str) -> float:
        """Retorna parametro de ataque. Si el equipo no esta en modelo, usa media."""
        return self.attack_params.get(team, 1.0)

    def _get_defense(self, team: str) -> float:
        """Retorna parametro de defensa. Si no esta en modelo, usa media."""
        return self.defense_params.get(team, 1.0)

    def _elo_strength_ratio(self, team1: str, team2: str) -> float:
        """Ratio de fortaleza relativa basado en parametros de ataque."""
        att1 = self._get_attack(team1)
        att2 = self._get_attack(team2)
        return att1 / (att1 + att2)

    def team_strengths(self) -> pd.DataFrame:
        """Retorna DataFrame con los parametros de cada equipo, ordenado por fortaleza."""
        if not self._is_fitted:
            return pd.DataFrame()

        records = []
        for team in self.teams:
            att = self.attack_params[team]
            def_ = self.defense_params[team]
            records.append({
                "team": team,
                "attack": round(att, 4),
                "defense": round(def_, 4),
                "net_strength": round(att / def_, 4),
            })

        df = pd.DataFrame(records).sort_values("net_strength", ascending=False)
        df["rank"] = range(1, len(df) + 1)
        return df.reset_index(drop=True)

    def print_top_teams(self, n: int = 20):
        """Imprime los N equipos mas fuertes segun el modelo."""
        df = self.team_strengths().head(n)
        print(f"\n{'RANKING':>5} {'EQUIPO':<25} {'ATAQUE':>8} {'DEFENSA':>8} {'NETO':>8}")
        print("-" * 60)
        for _, row in df.iterrows():
            print(f"{row['rank']:>5}  {row['team']:<25} {row['attack']:>8.4f} "
                  f"{row['defense']:>8.4f} {row['net_strength']:>8.4f}")

    def get_score_probabilities_table(self, home_team: str, away_team: str,
                                      max_goals: int = 5) -> pd.DataFrame:
        """Retorna tabla de probabilidades de marcadores como DataFrame."""
        matrix = self.predict_score_matrix(home_team, away_team,
                                           neutral=True, max_goals=max_goals)
        rows = []
        for i in range(max_goals + 1):
            for j in range(max_goals + 1):
                rows.append({
                    "home_goals": i,
                    "away_goals": j,
                    "score": f"{i}-{j}",
                    "probability": round(float(matrix[i, j]), 4),
                    "pct": f"{100 * float(matrix[i, j]):.2f}%",
                })

        df = pd.DataFrame(rows).sort_values("probability", ascending=False)
        return df.reset_index(drop=True)
