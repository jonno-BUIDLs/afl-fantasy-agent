"""KOLAgent — drafts X/Twitter posts for AFL Fantasy content."""
from afl_fantasy.agents.base import BaseAgent
from afl_fantasy.config import SONNET


# Post templates / content types
POST_TYPES = {
    "trade_target": "Trade target recommendation",
    "captain": "Captain/VC pick",
    "price_rise": "Price rise alert",
    "price_fall": "Price fall warning",
    "differential": "Differential/POD pick",
    "matchup": "Matchup analysis",
    "injury": "Injury/selection news reaction",
    "thread_intro": "Weekly round preview thread opener",
}

# Voice: punchy, confident, data-backed, no excessive hashtags
SYSTEM_PROMPT = """You are writing X (Twitter) posts for an AFL Fantasy KOL account.

Voice: confident, punchy, data-first, conversational. Like a sharp analyst who's done their homework.
Format rules:
- Max 280 characters per tweet
- Use emojis sparingly (1-2 max)
- Lead with the insight, not the preamble
- End with a question or hook when appropriate
- Use #AFLFantasy and 1 other relevant hashtag max
- No "🧵 Thread" unless it's the thread opener
- Stats should be concrete: use actual numbers, not vague language
- Don't start with "I think" or "In my opinion"

Always return just the tweet text, nothing else."""


class KOLAgent(BaseAgent):

    def __init__(self):
        super().__init__(model=SONNET)

    def draft_post(self, post_type: str, context: str) -> str:
        """Draft a single tweet. Returns the tweet text."""
        type_desc = POST_TYPES.get(post_type, post_type)
        prompt = f"""Draft a {type_desc} tweet for AFL Fantasy.

Context / data:
{context}

Return only the tweet text (≤280 chars)."""
        return self.ask(system=SYSTEM_PROMPT, user=prompt)

    def draft_round_preview_thread(
        self,
        round_name: str,
        trade_advice: str,
        captain_advice: str,
        matchup_highlights: str,
        differentials: str,
    ) -> list[str]:
        """Draft a 5-6 tweet thread for the round preview."""
        prompt = f"""Draft a 5-tweet AFL Fantasy thread for {round_name}.

Trade advice context:
{trade_advice}

Captain picks:
{captain_advice}

Matchup highlights:
{matchup_highlights}

Differential plays:
{differentials}

Return exactly 5 tweets, separated by the delimiter ---TWEET---
Each tweet ≤280 characters.
Tweet 1: Hook/intro (start with something that grabs attention)
Tweet 2: Captain/VC pick with data
Tweet 3: Trade targets or price rises
Tweet 4: Matchup angle or differential
Tweet 5: Summary + engagement question"""

        raw = self.ask(system=SYSTEM_PROMPT, user=prompt)
        tweets = [t.strip() for t in raw.split("---TWEET---") if t.strip()]
        return tweets

    def draft_injury_reaction(self, player_name: str, news: str, fantasy_impact: str) -> str:
        """React to breaking injury/selection news."""
        context = f"Player: {player_name}\nNews: {news}\nFantasy impact: {fantasy_impact}"
        return self.draft_post("injury", context)

    def draft_price_alert(self, player_name: str, team: str, position: str,
                          current_price: int, be: int, last3_avg: float,
                          direction: str) -> str:
        """Price rise or fall alert tweet."""
        post_type = "price_rise" if direction == "up" else "price_fall"
        context = (
            f"{player_name} ({team}, {position}) "
            f"Price: ${current_price/1000:.0f}k | BE: {be} | L3 avg: {last3_avg} "
            f"Direction: {direction}"
        )
        return self.draft_post(post_type, context)
