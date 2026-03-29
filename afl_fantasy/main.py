"""CLI entry point."""
import sys
import asyncio
from loguru import logger


def main():
    if len(sys.argv) < 2:
        print(
            "AFL Fantasy Agent\n"
            "Usage:\n"
            "  afl-agent brief          — run full pre-round brief now\n"
            "  afl-agent sync           — sync data only\n"
            "  afl-agent schedule       — start the scheduler daemon\n"
            "  afl-agent captain        — quick captain pick only\n"
            "  afl-agent bot            — start Telegram bot for approvals\n"
        )
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "brief":
        from afl_fantasy.orchestrator import run_pre_round_brief
        trades = int(sys.argv[2]) if len(sys.argv) > 2 else 2
        run_pre_round_brief(num_trades=trades)

    elif cmd == "sync":
        from afl_fantasy.orchestrator import sync_data
        players, rounds = sync_data()
        logger.info(f"Synced {len(players)} players, {len(rounds)} rounds")

    elif cmd == "schedule":
        from afl_fantasy.scheduler import start
        start()

    elif cmd == "captain":
        from afl_fantasy.data.fetcher import fetch_players, fetch_rounds
        from afl_fantasy.data.models import parse_player, parse_round
        from afl_fantasy.agents.classic_agent import ClassicAgent
        from afl_fantasy.orchestrator import get_current_round

        players = [parse_player(p) for p in fetch_players()]
        rounds = [parse_round(r) for r in fetch_rounds()]
        current = get_current_round(rounds)
        round_name = current.name if current else "Upcoming Round"

        agent = ClassicAgent()
        result = agent.captain_only(players, [], round_name)
        print(result)

    elif cmd == "bot":
        from afl_fantasy.notifications.telegram import build_bot_app
        app = build_bot_app()
        logger.info("Starting Telegram approval bot...")
        app.run_polling()

    else:
        logger.error(f"Unknown command: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
