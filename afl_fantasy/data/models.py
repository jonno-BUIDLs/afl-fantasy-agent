"""Pydantic models for AFL Fantasy data."""
from pydantic import BaseModel, field_validator
from typing import Optional
from afl_fantasy.config import SQUADS


class Player(BaseModel):
    id: int
    squad_id: int
    first_name: str
    last_name: str
    price: int
    status: str  # "playing", "injured", "suspended", "unavailable"
    positions: list[str]
    locked: bool
    games_played: int
    average_points: float
    total_points: int
    last3_avg: float
    last5_avg: float
    high_score: int
    low_score: int
    live_score: Optional[int] = None
    last_round_score: Optional[int] = None
    scores: dict[str, int]  # round_str -> score
    round_rank: Optional[int] = None
    season_rank: Optional[int] = None
    ownership: dict[str, float]  # round_str -> %
    round_price_change: int
    season_price_change: int
    prices: dict[str, int]  # round_str -> price

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def team(self) -> str:
        return SQUADS.get(self.squad_id, f"Squad{self.squad_id}")

    @property
    def price_str(self) -> str:
        return f"${self.price / 1000:.0f}k"

    @property
    def break_even(self) -> Optional[int]:
        """
        Approximate break-even from price trajectory.
        BE = (cost_to_maintain_price) derived from last price change.
        AFL Fantasy uses: BE = (previous_price - current_price) * factor + avg_score_needed
        Simplified: a player scores their BE to not drop in price next round.
        Real BE requires: 3-round rolling avg × 3 = totalPoints needed to hold price.
        We approximate: BE ≈ price / 7500 (rough heuristic, replace with real formula)
        """
        # Proper formula: BE = (sum_last3_scores_needed - sum_last2_actual)
        # where needed = price / 7500 * 3
        # Since we don't have exact AFL Fantasy formula coefficient confirmed,
        # use: BE ≈ round(price / 7500)
        return round(self.price / 7500)

    @property
    def score_list(self) -> list[int]:
        """Scores in round order."""
        return [v for _, v in sorted(self.scores.items(), key=lambda x: int(x[0]))]

    @property
    def latest_ownership(self) -> Optional[float]:
        if not self.ownership:
            return None
        latest_round = max(self.ownership.keys(), key=int)
        return self.ownership[latest_round]


class GameStats(BaseModel):
    player_id: int
    game_id: int
    round_number: int
    opponent_squad_id: int
    venue_id: int
    kicks: int
    handballs: int
    marks: int
    tackles: int
    frees_for: int
    frees_against: int
    hitouts: int
    goals: int
    behinds: int
    time_on_ground: int
    disposals: int
    inside50: int
    clearances: int
    clangers: int
    contested_possessions: int
    uncontested_possessions: int
    contested_marks: int
    goal_assist: int

    def fantasy_score(self) -> int:
        """Calculate AFL Fantasy score from raw stats."""
        from afl_fantasy.config import SCORING
        score = 0
        for stat, weight in SCORING.items():
            # Map snake_case field names to camelCase scoring keys
            field_map = {
                "kicks": self.kicks,
                "handballs": self.handballs,
                "marks": self.marks,
                "tackles": self.tackles,
                "freesFor": self.frees_for,
                "freesAgainst": self.frees_against,
                "hitouts": self.hitouts,
                "goals": self.goals,
                "behinds": self.behinds,
                "goalAssist": self.goal_assist,
                "inside50": self.inside50,
                "clearances": self.clearances,
                "clangers": self.clangers,
            }
            score += field_map.get(stat, 0) * weight
        return score


class Round(BaseModel):
    id: int
    round_number: int
    name: str
    status: str  # "completed", "playing", "scheduled"
    start_date: str
    end_date: str
    is_bye_round: bool
    bye_squads: list[int]
    games: list[dict]

    @property
    def is_completed(self) -> bool:
        return self.status == "completed"

    @property
    def is_live(self) -> bool:
        return self.status == "playing"

    @property
    def teams_on_bye(self) -> list[str]:
        return [SQUADS.get(sq, str(sq)) for sq in self.bye_squads]


def parse_player(raw: dict) -> Player:
    return Player(
        id=raw["id"],
        squad_id=raw["squadId"],
        first_name=raw["firstName"],
        last_name=raw["lastName"],
        price=raw["price"],
        status=raw.get("status", "playing"),
        positions=raw.get("position", []),
        locked=raw.get("locked", False),
        games_played=raw.get("gamesPlayed", 0),
        average_points=raw.get("averagePoints", 0.0),
        total_points=raw.get("totalPoints", 0),
        last3_avg=raw.get("last3Avg", 0.0),
        last5_avg=raw.get("last5Avg", 0.0),
        high_score=raw.get("highScore", 0),
        low_score=raw.get("lowScore", 0),
        live_score=raw.get("liveScore"),
        last_round_score=raw.get("lastRoundScore"),
        scores={str(k): v for k, v in raw.get("scores", {}).items()},
        round_rank=raw.get("roundRank"),
        season_rank=raw.get("seasonRank"),
        ownership={str(k): v for k, v in raw.get("ownership", {}).items()},
        round_price_change=raw.get("roundPriceChange", 0),
        season_price_change=raw.get("seasonPriceChange", 0),
        prices={str(k): v for k, v in raw.get("prices", {}).items()},
    )


def parse_game_stats(raw: dict) -> GameStats:
    return GameStats(
        player_id=raw["playerId"],
        game_id=raw["gameId"],
        round_number=raw["roundNumber"],
        opponent_squad_id=raw["opponentSquadId"],
        venue_id=raw["venueId"],
        kicks=raw.get("kicks", 0),
        handballs=raw.get("handballs", 0),
        marks=raw.get("marks", 0),
        tackles=raw.get("tackles", 0),
        frees_for=raw.get("freesFor", 0),
        frees_against=raw.get("freesAgainst", 0),
        hitouts=raw.get("hitouts", 0),
        goals=raw.get("goals", 0),
        behinds=raw.get("behinds", 0),
        time_on_ground=raw.get("timeOnGround", 0),
        disposals=raw.get("disposals", 0),
        inside50=raw.get("inside50", 0),
        clearances=raw.get("clearances", 0),
        clangers=raw.get("clangers", 0),
        contested_possessions=raw.get("contestedPossessions", 0),
        uncontested_possessions=raw.get("uncontestedPossessions", 0),
        contested_marks=raw.get("contestedMarks", 0),
        goal_assist=raw.get("goalAssist", 0),
    )


def parse_round(raw: dict) -> Round:
    return Round(
        id=raw["id"],
        round_number=raw["roundNumber"],
        name=raw["name"],
        status=raw["status"],
        start_date=raw["startDate"],
        end_date=raw["endDate"],
        is_bye_round=raw.get("isByeRound", False),
        bye_squads=raw.get("byeSquads", []),
        games=raw.get("games", []),
    )
