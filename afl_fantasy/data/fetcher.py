"""Raw data fetching from AFL Fantasy endpoints."""
import httpx
from loguru import logger
from afl_fantasy.config import (
    PLAYERS_URL, ROUNDS_URL, GAME_STATS_URL, AFL_FANTASY_COOKIE
)

# Headers that mimic a real browser session
_BASE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-AU,en;q=0.9",
    "Referer": "https://fantasy.afl.com.au/",
    "Origin": "https://fantasy.afl.com.au",
}


def _auth_headers() -> dict:
    headers = dict(_BASE_HEADERS)
    if AFL_FANTASY_COOKIE:
        headers["Cookie"] = AFL_FANTASY_COOKIE
    return headers


def fetch_players() -> list[dict]:
    """Fetch full player list (requires auth cookie)."""
    with httpx.Client(timeout=30) as client:
        r = client.get(PLAYERS_URL, headers=_auth_headers())
        r.raise_for_status()
        data = r.json()
        logger.info(f"Fetched {len(data)} players")
        return data


def fetch_rounds() -> list[dict]:
    """Fetch full season fixture (public)."""
    with httpx.Client(timeout=30) as client:
        r = client.get(ROUNDS_URL, headers=_BASE_HEADERS)
        r.raise_for_status()
        data = r.json()
        logger.info(f"Fetched {len(data)} rounds")
        return data


def fetch_player_game_stats(player_id: int) -> list[dict]:
    """Fetch per-game stats for a single player (public)."""
    url = GAME_STATS_URL.format(player_id=player_id)
    with httpx.Client(timeout=30) as client:
        r = client.get(url, headers=_BASE_HEADERS)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        return r.json()


def fetch_all_game_stats(player_ids: list[int], max_concurrent: int = 10) -> dict[int, list[dict]]:
    """Fetch game stats for multiple players concurrently."""
    import asyncio

    async def _fetch_one(client: httpx.AsyncClient, pid: int) -> tuple[int, list[dict]]:
        url = GAME_STATS_URL.format(player_id=pid)
        try:
            r = await client.get(url, headers=_BASE_HEADERS)
            if r.status_code == 404:
                return pid, []
            r.raise_for_status()
            return pid, r.json()
        except Exception as e:
            logger.warning(f"Failed to fetch stats for player {pid}: {e}")
            return pid, []

    async def _run():
        limits = httpx.Limits(max_connections=max_concurrent)
        async with httpx.AsyncClient(timeout=30, limits=limits) as client:
            tasks = [_fetch_one(client, pid) for pid in player_ids]
            results = await asyncio.gather(*tasks)
        return dict(results)

    return asyncio.run(_run())
