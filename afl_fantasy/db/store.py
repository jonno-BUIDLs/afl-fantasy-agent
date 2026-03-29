"""Supabase persistence layer."""
from supabase import create_client, Client
from loguru import logger
from afl_fantasy.config import SUPABASE_URL, SUPABASE_KEY
from afl_fantasy.data.models import Player, GameStats, Round

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


# ── Players ──────────────────────────────────────────────────────────────────

def upsert_players(players: list[Player]) -> None:
    rows = [
        {
            "id": p.id,
            "squad_id": p.squad_id,
            "first_name": p.first_name,
            "last_name": p.last_name,
            "price": p.price,
            "status": p.status,
            "positions": p.positions,
            "games_played": p.games_played,
            "average_points": p.average_points,
            "total_points": p.total_points,
            "last3_avg": p.last3_avg,
            "last5_avg": p.last5_avg,
            "high_score": p.high_score,
            "low_score": p.low_score,
            "live_score": p.live_score,
            "last_round_score": p.last_round_score,
            "scores": p.scores,
            "ownership": p.ownership,
            "round_price_change": p.round_price_change,
            "season_price_change": p.season_price_change,
            "prices": p.prices,
        }
        for p in players
    ]
    get_client().table("players").upsert(rows).execute()
    logger.info(f"Upserted {len(rows)} players")


def get_all_players() -> list[dict]:
    result = get_client().table("players").select("*").execute()
    return result.data


def get_players_by_position(position: str) -> list[dict]:
    result = (
        get_client()
        .table("players")
        .select("*")
        .contains("positions", [position])
        .execute()
    )
    return result.data


# ── Game Stats ───────────────────────────────────────────────────────────────

def upsert_game_stats(stats_list: list[GameStats]) -> None:
    rows = [
        {
            "player_id": s.player_id,
            "game_id": s.game_id,
            "round_number": s.round_number,
            "opponent_squad_id": s.opponent_squad_id,
            "venue_id": s.venue_id,
            "kicks": s.kicks,
            "handballs": s.handballs,
            "marks": s.marks,
            "tackles": s.tackles,
            "frees_for": s.frees_for,
            "frees_against": s.frees_against,
            "hitouts": s.hitouts,
            "goals": s.goals,
            "behinds": s.behinds,
            "time_on_ground": s.time_on_ground,
            "disposals": s.disposals,
            "inside50": s.inside50,
            "clearances": s.clearances,
            "clangers": s.clangers,
            "contested_possessions": s.contested_possessions,
            "uncontested_possessions": s.uncontested_possessions,
            "contested_marks": s.contested_marks,
            "goal_assist": s.goal_assist,
            "fantasy_score": s.fantasy_score(),
        }
        for s in stats_list
    ]
    get_client().table("game_stats").upsert(rows).execute()
    logger.info(f"Upserted {len(rows)} game stat rows")


def get_player_game_stats(player_id: int) -> list[dict]:
    result = (
        get_client()
        .table("game_stats")
        .select("*")
        .eq("player_id", player_id)
        .order("round_number")
        .execute()
    )
    return result.data


# ── PAA (Points Against by Position) ─────────────────────────────────────────

def get_paa_by_team(position: str, num_rounds: int = 5) -> dict[int, float]:
    """
    Returns {squad_id: avg_fantasy_points_conceded} for the given position
    over the last N completed rounds.
    Queries game_stats joined with players to get opponent squad conceding.
    """
    # We need: for each game, what fantasy score did position players score AGAINST each opponent?
    # game_stats.opponent_squad_id = the team being defended against
    # game_stats.fantasy_score = what the position player scored
    # Filter by players.positions containing the given position
    result = (
        get_client()
        .rpc("get_paa_by_team", {"position_filter": position, "num_rounds": num_rounds})
        .execute()
    )
    return {row["opponent_squad_id"]: row["avg_score"] for row in result.data}
