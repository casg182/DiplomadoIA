"""
FUENTES DE DATOS PARA EL MODELO DE PREDICCION - MUNDIAL 2026
=============================================================
Todas las fuentes son gratuitas y no requieren API KEY.
Los datos se descargan manualmente o via scraping local.

INSTRUCCIONES DE DESCARGA:
---------------------------
1. Descargar los archivos CSV/JSON en la carpeta data/raw/
2. Ejecutar preprocessing.py para limpiar y unificar los datos
3. Los datos procesados quedan en data/processed/
"""

# ─────────────────────────────────────────────────────────────────────────────
# FUENTE 1: RESULTADOS HISTORICOS INTERNACIONALES (LA MAS IMPORTANTE)
# ─────────────────────────────────────────────────────────────────────────────
SOURCE_1 = {
    "nombre": "International football results 1872-2024",
    "url_kaggle": "https://www.kaggle.com/datasets/martj42/international-football-results-from-1872-to-2017",
    "archivo_descarga": "results.csv",
    "destino_local": "data/raw/international_results.csv",
    "descripcion": (
        "Mas de 47,000 partidos internacionales desde 1872. "
        "Contiene: fecha, equipo local, equipo visitante, goles local, "
        "goles visitante, torneo, ciudad, pais, partido neutral."
    ),
    "columnas_clave": [
        "date", "home_team", "away_team", "home_score", "away_score",
        "tournament", "city", "country", "neutral"
    ],
    "requiere_cuenta": "Kaggle (gratuita)",
    "formato": "CSV",
    "tamano_aprox": "5 MB",
}

# ─────────────────────────────────────────────────────────────────────────────
# FUENTE 2: RANKING FIFA HISTORICO
# ─────────────────────────────────────────────────────────────────────────────
SOURCE_2 = {
    "nombre": "FIFA World Rankings histórico",
    "url_kaggle": "https://www.kaggle.com/datasets/cashncarry/fifaworldranking",
    "url_oficial": "https://www.fifa.com/fifa-world-ranking/men",
    "archivo_descarga": "fifa_ranking-2024-10-24.csv",
    "destino_local": "data/raw/fifa_rankings.csv",
    "descripcion": (
        "Ranking FIFA mensual desde 1992. "
        "Contiene: fecha, seleccion, puntos FIFA, posicion, variacion."
    ),
    "columnas_clave": [
        "rank_date", "country_full", "country_abrv", "total_points",
        "previous_points", "rank", "rank_change", "confederation"
    ],
    "requiere_cuenta": "Kaggle (gratuita)",
    "formato": "CSV",
    "tamano_aprox": "2 MB",
}

# ─────────────────────────────────────────────────────────────────────────────
# FUENTE 3: ESTADISTICAS AVANZADAS (xG, POSESION, PASES)
# ─────────────────────────────────────────────────────────────────────────────
SOURCE_3 = {
    "nombre": "StatsBomb Open Data",
    "url_github": "https://github.com/statsbomb/open-data",
    "descripcion": (
        "Datos de eventos a nivel de jugador (passes, shots, carries). "
        "Incluye xG (Expected Goals), presion, recuperaciones. "
        "Cubre Copas del Mundo 1930-2022, Eurocopas, Champions League."
    ),
    "comando_descarga": "git clone https://github.com/statsbomb/open-data.git data/raw/statsbomb",
    "archivos_relevantes": [
        "data/raw/statsbomb/data/matches/",  # partidos por competicion
        "data/raw/statsbomb/data/events/",   # eventos por partido
        "data/raw/statsbomb/data/lineups/",  # alineaciones
    ],
    "requiere_cuenta": "No",
    "formato": "JSON",
    "tamano_aprox": "4 GB completo / 500 MB solo mundiales",
}

# ─────────────────────────────────────────────────────────────────────────────
# FUENTE 4: ELO RATINGS DE SELECCIONES
# ─────────────────────────────────────────────────────────────────────────────
SOURCE_4 = {
    "nombre": "World Football Elo Ratings",
    "url": "https://www.eloratings.net/",
    "url_descarga_directa": "https://www.eloratings.net/World.tsv",
    "destino_local": "data/raw/elo_ratings.tsv",
    "descripcion": (
        "Rating Elo actualizado para todas las selecciones nacionales. "
        "Similar al sistema de ajedrez, refleja la fortaleza real. "
        "Descarga directa sin registro."
    ),
    "columnas_clave": ["rank", "country", "rating", "confederation"],
    "requiere_cuenta": "No",
    "formato": "TSV",
    "tamano_aprox": "< 1 MB",
}

# ─────────────────────────────────────────────────────────────────────────────
# FUENTE 5: ESTADISTICAS DE JUGADORES (CALIDAD DE PLANTILLA)
# ─────────────────────────────────────────────────────────────────────────────
SOURCE_5 = {
    "nombre": "FBref - Football Reference",
    "url": "https://fbref.com/en/country/players/",
    "descripcion": (
        "Estadisticas detalladas por jugador y seleccion nacional. "
        "xG, xA, progresion, presion, duelos aereos, etc. "
        "Permite scraping educativo."
    ),
    "url_nacionales": "https://fbref.com/en/squads/",
    "nota": "Scraping directo sin API key. Respetar rate limits (1 req/5s).",
    "columnas_relevantes": [
        "player", "nation", "pos", "age", "mp", "starts",
        "gls", "ast", "xG", "xAG", "progressive_carries",
        "tackles_won", "interceptions", "aerials_won_pct"
    ],
    "requiere_cuenta": "No",
    "formato": "HTML (scraping)",
}

# ─────────────────────────────────────────────────────────────────────────────
# FUENTE 6: HISTORIAL MUNDIALES FIFA
# ─────────────────────────────────────────────────────────────────────────────
SOURCE_6 = {
    "nombre": "FIFA World Cup - Kaggle Complete Dataset",
    "url_kaggle": "https://www.kaggle.com/datasets/abecklas/fifa-world-cup",
    "archivos": ["WorldCups.csv", "WorldCupMatches.csv", "WorldCupPlayers.csv"],
    "destino_local": "data/raw/world_cup_history/",
    "descripcion": (
        "Historial completo de mundiales 1930-2018. "
        "Partidos, goleadores, asistentes, tarjetas, estadios."
    ),
    "requiere_cuenta": "Kaggle (gratuita)",
    "formato": "CSV",
    "tamano_aprox": "2 MB",
}

# ─────────────────────────────────────────────────────────────────────────────
# FUENTE 7: RENDIMIENTO EN CLASIFICATORIAS 2026
# ─────────────────────────────────────────────────────────────────────────────
SOURCE_7 = {
    "nombre": "Resultados Eliminatorias 2026",
    "url_rsssf": "https://www.rsssf.org/tables/",
    "url_eleven_v_eleven": "https://www.11v11.com/international/",
    "descripcion": (
        "Resultados de todas las eliminatorias por confederation. "
        "Clave para medir forma reciente y nivel competitivo actual. "
        "RSSSF tiene archivos .txt descargables por confederacion."
    ),
    "confederaciones": {
        "UEFA": "https://www.rsssf.org/tables/26euq.html",
        "CONMEBOL": "https://www.rsssf.org/tables/26samq.html",
        "CONCACAF": "https://www.rsssf.org/tables/26concq.html",
        "CAF": "https://www.rsssf.org/tables/26afq.html",
        "AFC": "https://www.rsssf.org/tables/26asiq.html",
        "OFC": "https://www.rsssf.org/tables/26ocq.html",
    },
    "requiere_cuenta": "No",
    "formato": "HTML / TXT",
}

# ─────────────────────────────────────────────────────────────────────────────
# FUENTE 8: VALOR DE MERCADO DE PLANTILLAS
# ─────────────────────────────────────────────────────────────────────────────
SOURCE_8 = {
    "nombre": "Transfermarkt - Market Values",
    "url": "https://www.transfermarkt.com/nationalmannschaft/",
    "url_scraping": "https://www.transfermarkt.com/wettbewerbe/nationalmannschaft/wettbewerb/WM26",
    "descripcion": (
        "Valor de mercado por seleccion y jugador. "
        "Proxy de calidad de plantilla. Actualizado en tiempo real."
    ),
    "nota": "Scraping educativo. Headers necesarios para evitar bloqueo.",
    "headers_recomendados": {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "es-ES,es;q=0.9",
    },
    "requiere_cuenta": "No",
    "formato": "HTML (scraping)",
}

# ─────────────────────────────────────────────────────────────────────────────
# DESCRIPCION DE VARIABLES DEL MODELO
# ─────────────────────────────────────────────────────────────────────────────
MODEL_VARIABLES = {
    "fortaleza_ofensiva": {
        "descripcion": "Promedio de goles anotados (ponderado por recencia y rival)",
        "fuente": "SOURCE_1",
        "peso_modelo": "Alto",
    },
    "fortaleza_defensiva": {
        "descripcion": "Promedio de goles recibidos (ponderado por recencia y rival)",
        "fuente": "SOURCE_1",
        "peso_modelo": "Alto",
    },
    "ranking_fifa": {
        "descripcion": "Posicion y puntos en el ranking FIFA oficial",
        "fuente": "SOURCE_2",
        "peso_modelo": "Medio",
    },
    "rating_elo": {
        "descripcion": "Rating Elo del equipo (mejor calibrado que FIFA ranking)",
        "fuente": "SOURCE_4",
        "peso_modelo": "Alto",
    },
    "xg_promedio": {
        "descripcion": "Expected Goals promedio por partido (mide calidad de ocasiones)",
        "fuente": "SOURCE_3 / SOURCE_5",
        "peso_modelo": "Alto",
    },
    "xga_promedio": {
        "descripcion": "Expected Goals Against promedio (mide solidez defensiva real)",
        "fuente": "SOURCE_3 / SOURCE_5",
        "peso_modelo": "Alto",
    },
    "forma_reciente": {
        "descripcion": "Resultados ultimos 10-15 partidos con decaimiento exponencial",
        "fuente": "SOURCE_1",
        "peso_modelo": "Medio-Alto",
    },
    "h2h_historico": {
        "descripcion": "Balance historico frente a cabeza a cabeza especifico",
        "fuente": "SOURCE_1",
        "peso_modelo": "Medio",
    },
    "experiencia_mundial": {
        "descripcion": "Participaciones previas y rendimiento historico en mundiales",
        "fuente": "SOURCE_6",
        "peso_modelo": "Medio",
    },
    "valor_plantilla": {
        "descripcion": "Valor de mercado total de la plantilla (proxy de calidad)",
        "fuente": "SOURCE_8",
        "peso_modelo": "Medio",
    },
    "rendimiento_clasificatoria": {
        "descripcion": "Goles/puntos en eliminatorias de calificacion al mundial",
        "fuente": "SOURCE_7",
        "peso_modelo": "Medio-Alto",
    },
    "dias_descanso": {
        "descripcion": "Dias entre partidos (impacto en fatiga)",
        "fuente": "Calendario WC2026",
        "peso_modelo": "Bajo",
    },
    "rivalidad_confederacion": {
        "descripcion": "Factor de nivel competitivo de la confederacion de origen",
        "fuente": "SOURCE_1 + SOURCE_2",
        "peso_modelo": "Medio",
    },
}


def print_data_guide():
    """Imprime la guia completa de fuentes de datos."""
    sources = [SOURCE_1, SOURCE_2, SOURCE_3, SOURCE_4,
               SOURCE_5, SOURCE_6, SOURCE_7, SOURCE_8]

    print("=" * 70)
    print("GUIA DE FUENTES DE DATOS - MODELO MUNDIAL 2026")
    print("=" * 70)

    for i, src in enumerate(sources, 1):
        print(f"\n[FUENTE {i}] {src['nombre']}")
        print("-" * 50)
        print(f"  Descripcion : {src['descripcion'][:100]}...")
        print(f"  Destino     : {src.get('destino_local', src.get('comando_descarga', 'Ver URL'))}")
        print(f"  Requiere    : {src['requiere_cuenta']}")
        print(f"  Formato     : {src['formato']}")

    print("\n" + "=" * 70)
    print("VARIABLES DEL MODELO")
    print("=" * 70)
    for var, info in MODEL_VARIABLES.items():
        print(f"\n  {var.upper()} [Peso: {info['peso_modelo']}]")
        print(f"    {info['descripcion']}")
        print(f"    Fuente: {info['fuente']}")


if __name__ == "__main__":
    print_data_guide()
