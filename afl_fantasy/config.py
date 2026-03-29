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
    10: "Adelaide",       # Taylor Walker, Rory Laird ✓
    20: "Brisbane",       # Dayne Zorko, Lachie Neale ✓
    30: "Carlton",        # George Hewett, Zac Williams ✓
    40: "Collingwood",    # Scott Pendlebury, Steele Sidebottom ✓
    50: "Essendon",       # Peter Wright, Jade Gresham ✓
    60: "Fremantle",      # Alex Pearce, Sam Switkowski ✓
    70: "Geelong",        # Patrick Dangerfield, Tom Stewart ✓
    80: "Hawthorn",       # Jack Gunston, Jarman Impey, Karl Amon ✓
    90: "Melbourne",      # Jake Melksham, Steven May ✓
    100: "North Melbourne",  # Aidan Corr ✓
    110: "Port Adelaide", # Ollie Wines, Aliir Aliir ✓
    120: "Richmond",      # Dion Prestia, Tom Lynch, Nick Vlastuin ✓
    130: "St Kilda",      # Bradley Hill ✓
    140: "Western Bulldogs",  # Tom Liberatore, Adam Treloar, Marcus Bontempelli ✓
    150: "West Coast",    # Jamie Cripps, Elliot Yeo ✓
    160: "Sydney",        # Dane Rampe, Harry Cunningham ✓
    1000: "Gold Coast",   # Jarrod Witts, Sam Collins ✓
    1010: "GWS",          # Stephen Coniglio, Lachie Whitfield ✓
}

SQUAD_NAME_TO_ID = {v: k for k, v in SQUADS.items()}

# Position display order
POSITIONS = ["DEF", "MID", "RUC", "FWD"]

CURRENT_YEAR = 2026
