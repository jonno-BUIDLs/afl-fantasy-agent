"""Central config and constants."""
import os
from dotenv import load_dotenv

load_dotenv()

# API keys
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
AFL_FANTASY_COOKIE = os.environ.get("AFL_FANTASY_COOKIE", "")

# AFL Fantasy endpoints
AFL_BASE = "https://fantasy.afl.com.au/json/fantasy"
PLAYERS_URL = f"{AFL_BASE}/players.json"
ROUNDS_URL = f"{AFL_BASE}/rounds.json"
GAME_STATS_URL = f"{AFL_BASE}/players_game_stats/2026/{{player_id}}.json"

# Models
HAIKU = "claude-haiku-4-5-20251001"
SONNET = "claude-sonnet-4-6"

# AFL Fantasy scoring weights (used for projected score calc from raw stats)
# Source: AFL Fantasy official scoring
SCORING = {
    "kicks": 3,
    "handballs": 2,
    "marks": 3,
    "tackles": 4,
    "freesFor": 1,
    "freesAgainst": -3,
    "hitouts": 1,
    "goals": 6,
    "behinds": 1,
    "goalAssist": 1,
    "inside50": 2,
    "clearances": 5,
    "clangers": -1,
}

# Squad ID → Team name mapping (derived from players.json cross-reference)
SQUADS = {
    10: "Adelaide",
    20: "Brisbane",
    30: "Carlton",
    40: "Collingwood",
    50: "Essendon",
    60: "Fremantle",
    70: "Geelong",
    80: "GWS",
    90: "Gold Coast",
    100: "Hawthorn",
    110: "Melbourne",
    120: "North Melbourne",
    130: "Port Adelaide",
    140: "Richmond",
    150: "St Kilda",
    160: "Sydney",
    1000: "West Coast",
    1010: "Western Bulldogs",
}

SQUAD_NAME_TO_ID = {v: k for k, v in SQUADS.items()}

# Position display order
POSITIONS = ["DEF", "MID", "RUC", "FWD"]

CURRENT_YEAR = 2026
