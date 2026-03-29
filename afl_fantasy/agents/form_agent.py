"""FormAnalysisAgent — rolling averages, ceiling/floor, consistency."""
from afl_fantasy.data.models import Player
from afl_fantasy.agents.base import BaseAgent
from afl_fantasy.config import HAIKU


class FormAnalysisAgent(BaseAgent):
    """Analyses player form from scores in players.json."""

    def __init__(self):
        super().__init__(model=HAIKU)

    # ── Pure calculations (no LLM needed) ────────────────────────────────────

    @staticmethod
    def rolling_avg(player: Player, n: int) -> float | None:
        scores = player.score_list
        if not scores:
            return None
        window = scores[-n:]
        return round(sum(window) / len(window), 1)

    @staticmethod
    def ceiling(player: Player) -> int:
        return player.high_score

    @staticmethod
    def floor(player: Player) -> int:
        return player.low_score

    @staticmethod
    def consistency(player: Player) -> float | None:
        """% of games scoring 80+ (arbitrary 'consistent' threshold)."""
        scores = player.score_list
        if not scores:
            return None
        return round(sum(1 for s in scores if s >= 80) / len(scores) * 100, 1)

    @staticmethod
    def trend(player: Player) -> str:
        """Up / Down / Stable based on last3 vs last5 avg."""
        l3 = player.last3_avg
        l5 = player.last5_avg
        if l3 > l5 + 5:
            return "↑ Trending Up"
        elif l3 < l5 - 5:
            return "↓ Trending Down"
        return "→ Stable"

    def form_summary(self, player: Player) -> dict:
        return {
            "player": player.full_name,
            "team": player.team,
            "positions": player.positions,
            "price": player.price_str,
            "last3": player.last3_avg,
            "last5": player.last5_avg,
            "avg": player.average_points,
            "ceiling": self.ceiling(player),
            "floor": self.floor(player),
            "consistency": self.consistency(player),
            "trend": self.trend(player),
            "break_even": player.break_even,
            "ownership": player.latest_ownership,
            "scores": player.score_list,
        }

    # ── LLM insight ──────────────────────────────────────────────────────────

    def analyse_players(self, players: list[Player], context: str = "") -> str:
        """Generate a plain-English form summary for a list of players."""
        summaries = [self.form_summary(p) for p in players]
        data_str = "\n".join(
            f"- {s['player']} ({s['team']}, {'/'.join(s['positions'])}): "
            f"L3={s['last3']} L5={s['last5']} Avg={s['avg']} "
            f"Ceil={s['ceiling']} Floor={s['floor']} "
            f"BE={s['break_even']} Own={s['ownership']}% {s['trend']}"
            for s in summaries
        )
        prompt = f"""You are an AFL Fantasy analyst. Analyse the following players' form data and provide concise, actionable insights.

{context}

Player Data:
{data_str}

Focus on:
1. Who is in exceptional form (last 3 well above season avg)
2. Who is trending down and may need to be traded
3. Price rise / fall candidates based on break-even vs recent scores
4. Ownership traps (high ownership + trending down = everyone holds a falling asset)

Keep it punchy and specific. Use the player's last name only after first mention."""

        return self.ask(
            system="You are an expert AFL Fantasy analyst. Be direct, specific, and actionable. No fluff.",
            user=prompt,
        )
