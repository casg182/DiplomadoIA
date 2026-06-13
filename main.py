"""
Mundial 2026 - Sistema de Prediccion de Marcadores
===================================================
Ejecutar:  python main.py
           python main.py --match "Argentina" "France"
           python main.py --export
           python main.py --sources
"""

import sys
import argparse
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")
sys.path.insert(0, str(Path(__file__).parent))

from src.data.data_sources import print_data_guide
from src.data.preprocessing import (
    load_match_results,
    load_elo_ratings,
    prepare_training_data,
    compute_team_stats,
)
from src.models.dixon_coles import DixonColesModel
from src.simulation.tournament import TournamentPredictor


def build_and_train_model(verbose: bool = True) -> DixonColesModel:
    """Carga datos, prepara features y entrena el modelo Dixon-Coles."""
    print("\n[1/3] Cargando datos historicos...")
    results_df = load_match_results()

    print("[2/3] Preparando datos de entrenamiento...")
    train_df = prepare_training_data(results_df, years=8)

    elo_df = load_elo_ratings()

    print("[3/3] Entrenando modelo Dixon-Coles...")
    model = DixonColesModel()
    model.fit(train_df)

    if verbose:
        print("\nFORTALEZA DE EQUIPOS (Top 15 segun modelo):")
        model.print_top_teams(15)

    return model


def predict_full_tournament(export: bool = False):
    """Ejecuta prediccion completa del Mundial 2026."""
    model = build_and_train_model()
    predictor = TournamentPredictor(model)
    predictions = predictor.run_full_prediction()

    if export:
        predictor.export_predictions()

    return predictor


def predict_single_match(team1: str, team2: str, knockout: bool = False):
    """Predice un partido especifico."""
    model = build_and_train_model(verbose=False)
    predictor = TournamentPredictor(model)
    predictor.predict_single_match(team1, team2, knockout=knockout)


def show_group(group_letter: str):
    """Muestra predicciones detalladas para un grupo especifico."""
    model = build_and_train_model(verbose=False)
    from src.simulation.tournament import GroupStageSimulator, load_tournament_data
    from src.data.preprocessing import compute_team_stats

    data = load_tournament_data()
    if group_letter.upper() not in data["groups"]:
        print(f"[ERROR] Grupo '{group_letter}' no encontrado. Grupos disponibles: A-L")
        return

    sim = GroupStageSimulator(model, data)
    standings = sim.simulate_group(group_letter.upper())

    print(f"\nPREDICCION DETALLADA - GRUPO {group_letter.upper()}")
    print("=" * 60)
    teams = data["groups"][group_letter.upper()]["teams"]

    print("\nPARTIDOS DEL GRUPO:")
    from itertools import combinations
    for home, away in combinations(teams, 2):
        pred = model.predict_outcome(home, away, neutral=True)
        print(f"\n  {home} vs {away}")
        print(f"    Victoria {home[:20]}: {pred['home_win_prob']*100:.1f}%")
        print(f"    Empate              : {pred['draw_prob']*100:.1f}%")
        print(f"    Victoria {away[:20]}: {pred['away_win_prob']*100:.1f}%")
        print(f"    Marcador probable   : {pred['most_likely_score']}")

    print(f"\nTABLA FINAL PREDICHA - GRUPO {group_letter.upper()}:")
    print(f"{'POS':<4} {'EQUIPO':<25} {'PTS':>4} {'GF':>4} {'GC':>4} {'DG':>4}")
    print("-" * 45)
    for _, row in standings.iterrows():
        q = "-> CLASIFICA" if row["pos"] <= 2 else ""
        print(f"{row['pos']:<4} {row['team']:<25} {row['pts']:>4} "
              f"{row['gf']:>4} {row['gc']:>4} {row['gd']:>4}  {q}")


def main():
    parser = argparse.ArgumentParser(
        description="Mundial 2026 - Sistema de Prediccion de Marcadores"
    )
    parser.add_argument(
        "--match", nargs=2, metavar=("EQUIPO1", "EQUIPO2"),
        help="Predice un partido especifico. Ej: --match Argentina France"
    )
    parser.add_argument(
        "--knockout", action="store_true",
        help="Tratar partido como eliminatoria (con posibilidad de penaltis)"
    )
    parser.add_argument(
        "--group", metavar="LETRA",
        help="Predice un grupo completo. Ej: --group A"
    )
    parser.add_argument(
        "--full", action="store_true",
        help="Predice el torneo completo (104 partidos)"
    )
    parser.add_argument(
        "--export", action="store_true",
        help="Exportar predicciones a Excel (usar con --full)"
    )
    parser.add_argument(
        "--sources", action="store_true",
        help="Muestra la guia de fuentes de datos"
    )
    parser.add_argument(
        "--strengths", action="store_true",
        help="Muestra ranking de fortaleza de todos los equipos"
    )

    args = parser.parse_args()

    if args.sources:
        print_data_guide()
        return

    if args.match:
        predict_single_match(args.match[0], args.match[1], knockout=args.knockout)
        return

    if args.group:
        show_group(args.group)
        return

    if args.strengths:
        model = build_and_train_model(verbose=False)
        print("\nRANKING COMPLETO DE FORTALEZA POR EQUIPO:")
        model.print_top_teams(50)
        return

    if args.full or args.export:
        predict_full_tournament(export=args.export)
        return

    # Sin argumentos: ejecutar prediccion completa
    print("=" * 65)
    print("  MUNDIAL 2026 - SISTEMA DE PREDICCION")
    print("=" * 65)
    print("\nUso:")
    print("  python main.py --full              # Prediccion completa (104 partidos)")
    print("  python main.py --full --export     # + exportar a Excel")
    print("  python main.py --match Arg France  # Un partido especifico")
    print("  python main.py --group A           # Un grupo completo")
    print("  python main.py --sources           # Guia de fuentes de datos")
    print("  python main.py --strengths         # Ranking de equipos")
    print()
    print("Ejecutando prediccion completa por defecto...\n")
    predict_full_tournament(export=True)


if __name__ == "__main__":
    main()
