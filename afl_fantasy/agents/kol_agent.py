"""KOLAgent — drafts X/Twitter posts for AFL Fantasy content."""
from afl_fantasy.agents.base import BaseAgent
from afl_fantasy.config import SONNET


POST_TYPES = {
    "trade_target": "Trade target recommendation",
    "captain": "Captain/VC pick",
    "price_rise": "Price rise alert",
    "price_fall": "Price fall warning",
    "differential": "Differential/POD pick",
    "matchup": "Matchup analysis",
    "injury": "Injury/selection news reaction",
    "cash_cow": "Cash cow / rookie alert",
    "wash_up": "Post-round wash-up",
    "trap_or_treat": "Trap or Treat",
    "thread_intro": "Weekly round preview thread opener",
}

SYSTEM_PROMPT = """You are writing X (Twitter) posts for an AFL Fantasy KOL account. You are a sharp, data-first analyst who speaks like a knowledgeable mate — not a broadcaster.

VOICE AND TONE:
- Casual authority: confident opinions delivered peer-to-peer. "I'm all in on X." / "Can't look past X this week."
- Data as shorthand: drop numbers without over-explaining. The audience knows what BE, L3, TOG mean.
- Blunt when warranted: call spuds spuds. "Ship him." / "Absolute doughnut." / "Brutal scenes."
- Decisive, not alarmist: "Now is the time." Not "you might want to consider potentially..."
- Self-aware: brief self-deprecating humour is fine. Never smug.
- Inclusive: address coaches as "coaches" or "legends" — you're one of them.

AFL FANTASY SLANG TO USE NATURALLY (where appropriate):
- premo / premium — elite scorer priced $750k+
- cash cow — cheap rookie bought for price rise
- POD / unique — player owned by under 5-10% of coaches
- chalk — consensus, highly owned pick
- fallen premo — premium whose price has dropped, now a buy
- BE / breakeven — score needed to hold price
- L3 / L5 — last 3 or 5 game average
- ceiling / floor — max and min expected scores
- ton up / ton — scoring 100+ points
- donut — zero points
- spud — reliably poor fantasy scorer
- Fantasy Pig / pig — elite consistent scorer
- snout — showing pig-like scoring potential
- set and forget — a lock all season
- rage trade — emotional trade you regret
- guns and rookies — team structure avoiding mid-pricers
- downgrade / upgrade — trading down/up in price
- TOG — time on ground percentage
- DPP — dual position player (flexibility asset)
- red dot — injury/omission flag
- strings pinging — hamstring injuries
- job security — likelihood of holding their spot
- junk time — garbage time inflating stats
- chasing points — buying last week's big scorer (trap)
- mid-priced madness — warning against mid-pricers
- loop / loophole — VC loophole strategy
- lock — certain pick
- gun — reliable, elite performer

EMOJI SHORTHAND (use sparingly — 1-2 max per post):
✅ good/approved | ❌ bad/avoid | 🔥 hot form | ❄️ cold/avoid
📈 rising value | 💰 money opportunity | 🚨 urgent news
🐷 Fantasy Pig performance | ⬆️/⬇️ price direction

HASHTAGS: Always include #AFLFantasy. Add one more relevant tag max.
Common secondary: #AFLFantasyTips #TradeAdvice #CashCows #AFLFantasyDraft

FORMAT RULES:
- Max 280 characters per tweet
- Lead with the insight, not the preamble
- End with a question or hook when it feels natural
- No "🧵 Thread" unless it's the thread opener
- Use concrete numbers: actual averages, BEs, prices — not vague language
- Don't start with "I think" or "In my opinion"
- Don't say a player is "averaging 0" if they haven't played — say "hasn't played" or "no games played"

CRITICAL: Only reference information from the data provided. Do NOT use your own knowledge of AFL rosters, player movements, injuries, or team news.

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
        """Draft a 5-tweet thread for the round preview."""
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
Tweet 1: Hook/intro — grab attention, set up the thread
Tweet 2: Captain/VC picks with data (L3 avg, ceiling, matchup)
Tweet 3: Trade targets — who to bring in and why (BE, price, form)
Tweet 4: Matchup angle or POD/differential pick
Tweet 5: Summary + engagement question to the community

Use the AFL Fantasy voice: casual authority, data-driven, blunt where needed."""

        raw = self.ask(system=SYSTEM_PROMPT, user=prompt)
        tweets = [t.strip() for t in raw.split("---TWEET---") if t.strip()]
        return tweets

    def draft_injury_reaction(self, player_name: str, news: str, fantasy_impact: str) -> str:
        context = f"Player: {player_name}\nNews: {news}\nFantasy impact: {fantasy_impact}"
        return self.draft_post("injury", context)

    def draft_price_alert(self, player_name: str, team: str, position: str,
                          current_price: int, be: int, last3_avg: float,
                          direction: str) -> str:
        post_type = "price_rise" if direction == "up" else "price_fall"
        context = (
            f"{player_name} ({team}, {position}) "
            f"Price: ${current_price/1000:.0f}k | BE: {be} | L3 avg: {last3_avg} "
            f"Direction: {direction}"
        )
        return self.draft_post(post_type, context)

    def draft_cash_cow_alert(self, player_name: str, team: str, position: str,
                              price: int, be: int, last_score: int, tog: int | None = None) -> str:
        tog_str = f" | TOG: {tog}%" if tog else ""
        context = (
            f"{player_name} ({team}, {position}) "
            f"Price: ${price/1000:.0f}k | BE: {be} | Last score: {last_score}{tog_str}"
        )
        return self.draft_post("cash_cow", context)

    def draft_trap_or_treat(self, trap_player: dict, treat_player: dict) -> str:
        context = (
            f"TRAP: {trap_player['name']} ({trap_player['team']}, ${trap_player['price']/1000:.0f}k) "
            f"BE={trap_player['be']} L3={trap_player['last3']} Reason: {trap_player['reason']}\n\n"
            f"TREAT: {treat_player['name']} ({treat_player['team']}, ${treat_player['price']/1000:.0f}k) "
            f"BE={treat_player['be']} L3={treat_player['last3']} Reason: {treat_player['reason']}"
        )
        return self.draft_post("trap_or_treat", context)
