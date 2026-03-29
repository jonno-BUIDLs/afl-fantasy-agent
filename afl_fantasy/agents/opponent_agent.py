"""OpponentAgent — Points Against by Position (PAA) analysis."""
from collections import defaultdict
from afl_fantasy.data.models import Player, GameStats, Round
from afl_fantasy.agents.base import BaseAgent
from afl_fantasy.config import SQUADS, HAIKU


class OpponentAgent(BaseAgent):
    """
    Calculates PAA (Points Against by Position) — how many fantasy points
    each AFL team has conceded to each position group over the last N rounds.
    Higher PAA = easier matchup for that position.
    """

    def __init__(self):
        super().__init__(model=HAIKU)

    def calculate_paa(
        self,
        all_game_stats: dict[int, list[GameStats]],
        player_positions: dict[int, list[str]],  # player_id -> positions
        num_rounds: int = 5,
    ) -> dict[str, dict[int, float]]:
        """
        Returns: {position: {opponent_squad_id: avg_fantasy_pts_conceded}}
        """
        # Find max round so we can filter to last N
        all_rounds = [
            gs.round_number
            for stats in all_game_stats.values()
            for gs in stats
        ]
        if not all_rounds:
            return {}
        max_round = max(all_rounds)
        cutoff = max_round - num_rounds

        # Accumulate: position → opponent → [scores]
        paa_raw: dict[str, dict[int, list[int]]] = defaultdict(lambda: defaultdict(list))

        for player_id, stats in all_game_stats.items():
            positions = player_positions.get(player_id, [])
            for gs in stats:
                if gs.round_number <= cutoff:
                    continue
                score = gs.fantasy_score()
                for pos in positions:
                    paa_raw[pos][gs.opponent_squad_id].append(score)

        # Average
        result: dict[str, dict[int, float]] = {}
        for pos, opp_dict in paa_raw.items():
            result[pos] = {
                opp: round(sum(scores) / len(scores), 1)
                for opp, scores in opp_dict.items()
            }
        return result

    def matchup_ratings(
        self,
        paa: dict[str, dict[int, float]],
        upcoming_games: list[dict],  # [{home_squad_id, away_squad_id}, ...]
    ) -> list[dict]:
        """
        Given PAA data and upcoming fixtures, rank matchups.
        Returns list of {team, opponent, position, paa_score, rating} dicts.
        """
        ratings = []
        for game in upcoming_games:
            for home_away in ["home", "away"]:
                team_id = game[f"{home_away}Id"]
                opp_id = game["awayId" if home_away == "home" else "homeId"]
                for pos in ["DEF", "MID", "RUC", "FWD"]:
                    pos_paa = paa.get(pos, {})
                    if opp_id not in pos_paa:
                        continue
                    avg = pos_paa[opp_id]
                    ratings.append({
                        "team": SQUADS.get(team_id, str(team_id)),
                        "team_id": team_id,
                        "opponent": SQUADS.get(opp_id, str(opp_id)),
                        "opponent_id": opp_id,
                        "position": pos,
                        "paa_avg": avg,
                    })
        # Sort: best matchups first (highest PAA = most points conceded by opponent)
        ratings.sort(key=lambda x: x["paa_avg"], reverse=True)
        return ratings

    def analyse_matchups(self, ratings: list[dict], round_name: str = "this round") -> str:
        """LLM summary of the best and worst matchups."""
        top = ratings[:15]
        data_str = "\n".join(
            f"- {r['team']} vs {r['opponent']} ({r['position']}): "
            f"{r['opponent']} concedes avg {r['paa_avg']} pts to {r['position']}s"
            for r in top
        )
        prompt = f"""You are an AFL Fantasy analyst. Here are the top matchup opportunities for {round_name} based on Points Against by Position (PAA).

{data_str}

Summarise the key matchup advantages — which positions and teams to target, and why. Call out any standout 'smokey' matchups that might be under the radar."""

        return self.ask(
            system=(
                "You are an expert AFL Fantasy analyst. Be direct and actionable. "
                "CRITICAL: Only reference the matchup data provided. Do NOT use your own knowledge "
                "of AFL fixtures, team form, or player rosters beyond what is in the data."
            ),
            user=prompt,
        )
