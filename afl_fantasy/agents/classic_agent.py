"""ClassicAgent — trade targets, captain picks, differential plays."""
from afl_fantasy.data.models import Player
from afl_fantasy.agents.base import BaseAgent
from afl_fantasy.config import SONNET


class ClassicAgent(BaseAgent):
    """
    Synthesises form + matchup data into Classic Fantasy strategy:
    - Trade targets (who to bring in / who to trade out)
    - Captain recommendation
    - Differential picks (low ownership, high upside)
    - Price rise targets (BE below current avg)
    """

    def __init__(self):
        super().__init__(model=SONNET)

    def recommend(
        self,
        all_players: list[Player],
        paa_ratings: list[dict],
        round_name: str,
        my_team: list[int] | None = None,  # player IDs I currently own
        num_trades: int = 2,
    ) -> str:
        """Full Classic strategy brief for the upcoming round."""

        # Filter to playing, non-locked players
        available = [p for p in all_players if p.status == "playing"]

        # Price risers: BE < last3_avg by 10+ (going up)
        price_risers = [
            p for p in available
            if p.break_even and p.last3_avg > p.break_even + 10
        ]
        price_risers.sort(key=lambda p: p.last3_avg - (p.break_even or 0), reverse=True)

        # Price fallers: BE > last3_avg by 15+ (danger)
        price_fallers = [
            p for p in available
            if p.break_even and p.last3_avg < p.break_even - 15
        ]
        price_fallers.sort(key=lambda p: (p.break_even or 0) - p.last3_avg, reverse=True)

        # Captain candidates: high avg + good matchup
        captain_pool = sorted(available, key=lambda p: p.last3_avg, reverse=True)[:20]

        # Differentials: <5% ownership + avg > 90
        differentials = [
            p for p in available
            if (p.latest_ownership or 100) < 5 and p.average_points > 90
        ]
        differentials.sort(key=lambda p: p.average_points, reverse=True)

        def fmt_player(p: Player) -> str:
            be_str = f"BE={p.break_even}" if p.break_even else "BE=?"
            return (
                f"{p.full_name} ({p.team}, {'/'.join(p.positions)}) "
                f"${p.price/1000:.0f}k L3={p.last3_avg} Avg={p.average_points:.0f} "
                f"{be_str} Own={p.latest_ownership or '?'}%"
            )

        # Top matchup teams from PAA
        top_matchups = paa_ratings[:10] if paa_ratings else []
        matchup_str = "\n".join(
            f"  - {r['team']} vs {r['opponent']}: {r['position']}s face easy matchup (opp concedes {r['paa_avg']} avg)"
            for r in top_matchups
        ) or "  (no matchup data)"

        prompt = f"""You are my personal AFL Fantasy Classic coach. Give me my round strategy for {round_name}.

I have {num_trades} trades available.

PRICE RISERS (buy candidates — scoring above break-even):
{chr(10).join(fmt_player(p) for p in price_risers[:10]) or "None identified"}

PRICE FALLERS (sell candidates — danger of price drop):
{chr(10).join(fmt_player(p) for p in price_fallers[:8]) or "None identified"}

CAPTAIN CANDIDATES (top form):
{chr(10).join(fmt_player(p) for p in captain_pool[:12])}

DIFFERENTIALS (<5% ownership, avg 90+):
{chr(10).join(fmt_player(p) for p in differentials[:8]) or "None identified"}

BEST MATCHUPS THIS ROUND:
{matchup_str}

Give me:
1. **Trade Recommendations** ({num_trades} trades max) — who to trade out and who to bring in, with reasoning
2. **Captain Pick** — first choice and backup
3. **Differential Play** — one punt pick worth considering
4. **Keep an eye on** — 1-2 players whose situation could change pre-lockout

Be direct. Use player surnames after first mention. Flag if a trade target has a suspect injury history or VC opportunity."""

        return self.ask(
            system=(
                "You are an elite AFL Fantasy Classic coach. Provide concise, high-confidence advice. "
                "Never hedge excessively. Give one clear recommendation, not a list of maybes. "
                "CRITICAL: Only use the data provided. Do NOT use your own knowledge of AFL player "
                "movements, injuries, team changes, or fixtures. Treat all team/position data as current fact."
            ),
            user=prompt,
        )

    def captain_only(self, players: list[Player], paa_ratings: list[dict], round_name: str) -> str:
        """Quick captain/VC recommendation only."""
        top = sorted(
            [p for p in players if p.status == "playing"],
            key=lambda p: p.last3_avg,
            reverse=True,
        )[:15]

        # Find matchup boosts
        team_matchup: dict[str, float] = {}
        for r in paa_ratings:
            key = f"{r['team']}_{r['position']}"
            team_matchup[key] = r["paa_avg"]

        def matchup_bonus(p: Player) -> str:
            for pos in p.positions:
                key = f"{p.team}_{pos}"
                if key in team_matchup and team_matchup[key] > 100:
                    return f" [GREAT MATCHUP: opp concedes {team_matchup[key]:.0f} to {pos}s]"
            return ""

        data = "\n".join(
            f"- {p.full_name} ({p.team}, {'/'.join(p.positions)}): "
            f"L3={p.last3_avg} Ceil={p.high_score}{matchup_bonus(p)}"
            for p in top
        )

        return self.ask(
            system="You are an AFL Fantasy expert. Be extremely direct.",
            user=(
                f"Captain picks for {round_name}:\n\n{data}\n\n"
                f"Rank the top 5 captain options 1-5. For each give: player name, "
                f"one sentence rationale covering form + matchup + ceiling. "
                f"Then name your VC. Be direct, no fluff."
            ),
        )
