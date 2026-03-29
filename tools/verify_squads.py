"""
Prints all unique squadId values from players.json with known players,
so we can verify the SQUADS mapping in config.py is correct.

Usage (from project root with venv active):
    python tools/verify_squads.py
"""
from afl_fantasy.data.fetcher import fetch_players
from collections import defaultdict

players = fetch_players()

# Group players by squadId, show 2 well-known names per squad
squads = defaultdict(list)
for p in players:
    squads[p["squadId"]].append(f"{p['firstName']} {p['lastName']}")

print("squadId | Sample Players")
print("-" * 60)
for squad_id in sorted(squads.keys()):
    sample = ", ".join(squads[squad_id][:3])
    print(f"  {squad_id:<6} | {sample}")
