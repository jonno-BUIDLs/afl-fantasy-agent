"""
Main orchestrator — ties all agents together for a round brief.
Called by the scheduler or manually.
"""
import asyncio
from loguru import logger
from afl_fantasy.data.fetcher import fetch_players, fetch_rounds, fetch_all_game_stats
from afl_fantasy.data.models import parse_player, parse_round, parse_game_stats, Round
from afl_fantasy.db.store import upsert_players, upsert_game_stats, get_client
from afl_fantasy.agents.form_agent import FormAnalysisAgent
from afl_fantasy.agents.opponent_agent import OpponentAgent
from afl_fantasy.agents.classic_agent import ClassicAgent
from afl_fantasy.agents.kol_agent import KOLAgent
from afl_fantasy.notifications import telegram


def get_current_round(rounds: list[Round]) -> Round | None:
    """Find the current or next upcoming round."""
    playing = [r for r in rounds if r.is_live]
    if playing:
        return playing[0]
    upcoming = [r for r in rounds if r.status == "scheduled"]
    return upcoming[0] if upcoming else None


def sync_data() -> tuple[list, list[Round]]:
    """Fetch fresh data and persist to Supabase. Returns (players, rounds)."""
    logger.info("Syncing player data...")
    raw_players = fetch_players()
    players = [parse_player(p) for p in raw_players]
    upsert_players(players)

    logger.info("Syncing round data...")
    raw_rounds = fetch_rounds()
    rounds = [parse_round(r) for r in raw_rounds]

    # Sync rounds to DB
    rows = [
        {
            "id": r.id,
            "round_number": r.round_number,
            "name": r.name,
            "status": r.status,
            "start_date": r.start_date,
            "end_date": r.end_date,
            "is_bye_round": r.is_bye_round,
            "bye_squads": r.bye_squads,
            "games": r.games,
        }
        for r in rounds
    ]
    get_client().table("rounds").upsert(rows).execute()

    logger.info("Syncing game stats for all players...")
    player_ids = [p.id for p in players]
    raw_stats = fetch_all_game_stats(player_ids)

    all_stats = []
    for pid, stats_list in raw_stats.items():
        for s in stats_list:
            try:
                all_stats.append(parse_game_stats(s))
            except Exception as e:
                logger.warning(f"Failed to parse stat for player {pid}: {e}")
    if all_stats:
        upsert_game_stats(all_stats)

    return players, rounds


def run_pre_round_brief(num_trades: int = 2) -> None:
    """
    Full pre-round strategy brief:
    1. Sync all data
    2. Run form analysis
    3. Run PAA / matchup analysis
    4. Generate Classic strategy
    5. Draft KOL posts
    6. Send everything to Telegram
    """
    # 1. Data sync
    players, rounds = sync_data()
    current_round = get_current_round(rounds)
    round_name = current_round.name if current_round else "Upcoming Round"
    logger.info(f"Running brief for: {round_name}")

    # Build player_id -> positions map for PAA
    player_positions = {p.id: p.positions for p in players}

    # Get game stats from DB (already synced above)
    from afl_fantasy.db.store import get_all_players
    from afl_fantasy.data.models import GameStats

    # 2. Form analysis
    form_agent = FormAnalysisAgent()
    # Focus on premiums and potential trade targets
    top_players = sorted(
        [p for p in players if p.status == "playing" and p.games_played >= 2],
        key=lambda p: p.last3_avg,
        reverse=True,
    )[:30]
    form_brief = form_agent.analyse_players(top_players, context=f"Preparing for {round_name}")

    # 3. PAA / matchup analysis
    opp_agent = OpponentAgent()
    # We need game stats — pull from Supabase
    all_game_stats_raw = {}
    for p in players:
        from afl_fantasy.db.store import get_player_game_stats
        raw = get_player_game_stats(p.id)
        if raw:
            stats = []
            for row in raw:
                try:
                    gs = GameStats(
                        player_id=row["player_id"],
                        game_id=row["game_id"],
                        round_number=row["round_number"],
                        opponent_squad_id=row["opponent_squad_id"],
                        venue_id=row["venue_id"],
                        kicks=row["kicks"],
                        handballs=row["handballs"],
                        marks=row["marks"],
                        tackles=row["tackles"],
                        frees_for=row["frees_for"],
                        frees_against=row["frees_against"],
                        hitouts=row["hitouts"],
                        goals=row["goals"],
                        behinds=row["behinds"],
                        time_on_ground=row["time_on_ground"],
                        disposals=row["disposals"],
                        inside50=row["inside50"],
                        clearances=row["clearances"],
                        clangers=row["clangers"],
                        contested_possessions=row["contested_possessions"],
                        uncontested_possessions=row["uncontested_possessions"],
                        contested_marks=row["contested_marks"],
                        goal_assist=row["goal_assist"],
                    )
                    stats.append(gs)
                except Exception:
                    pass
            all_game_stats_raw[p.id] = stats

    paa = opp_agent.calculate_paa(all_game_stats_raw, player_positions)

    # Get upcoming games from current round
    upcoming_games = current_round.games if current_round else []
    paa_ratings = opp_agent.matchup_ratings(paa, upcoming_games)
    matchup_brief = opp_agent.analyse_matchups(paa_ratings, round_name)

    # 4. Classic strategy
    classic_agent = ClassicAgent()
    strategy = classic_agent.recommend(players, paa_ratings, round_name, num_trades=num_trades)

    # 5. KOL posts
    kol = KOLAgent()
    # Captain post
    captain_tweet = kol.draft_post("captain", strategy[:500])
    # Trade target post
    trade_tweet = kol.draft_post("trade_target", strategy[:500])

    # 6. Send to Telegram
    asyncio.run(_send_all(
        round_name=round_name,
        form_brief=form_brief,
        matchup_brief=matchup_brief,
        strategy=strategy,
        captain_tweet=captain_tweet,
        trade_tweet=trade_tweet,
    ))


async def _send_all(
    round_name: str,
    form_brief: str,
    matchup_brief: str,
    strategy: str,
    captain_tweet: str,
    trade_tweet: str,
) -> None:
    from afl_fantasy.db.store import get_client

    # Personal strategy brief (not for posting)
    full_brief = f"*FORM ANALYSIS*\n{form_brief}\n\n*MATCHUPS*\n{matchup_brief}\n\n*STRATEGY*\n{strategy}"
    await telegram.send_strategy_brief(full_brief, round_name)

    # Save draft posts to DB and send for approval
    supabase = get_client()

    for tweet, post_type in [(captain_tweet, "captain"), (trade_tweet, "trade_target")]:
        result = (
            supabase.table("posts")
            .insert({"content": tweet, "post_type": post_type, "status": "draft"})
            .execute()
        )
        post_id = result.data[0]["id"]
        await telegram.send_draft_post(tweet, post_type, post_id)
