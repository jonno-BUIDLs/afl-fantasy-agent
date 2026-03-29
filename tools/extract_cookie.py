"""
One-time tool to extract your AFL Fantasy session cookie using Playwright.
Run this locally once, copy the cookie to your .env, then Playwright is not needed again.

Usage:
    pip install playwright
    playwright install chromium
    python tools/extract_cookie.py
"""
import asyncio
from playwright.async_api import async_playwright


async def extract_cookie():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # visible browser
        page = await browser.new_page()

        print("Opening AFL Fantasy login page...")
        await page.goto("https://fantasy.afl.com.au/")

        print("\n>>> Log in manually in the browser window that opened.")
        print(">>> Once you can see the main AFL Fantasy dashboard, press ENTER here.")
        input()

        # Grab all cookies
        cookies = await page.context.cookies()
        await browser.close()

        # Find the relevant session cookie(s)
        cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)

        print("\n" + "="*60)
        print("COOKIE STRING (copy this to your .env as AFL_FANTASY_COOKIE):")
        print("="*60)
        print(cookie_str)
        print("="*60)

        # Also verify it works
        import httpx
        headers = {
            "Cookie": cookie_str,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Referer": "https://fantasy.afl.com.au/",
        }
        r = httpx.get("https://fantasy.afl.com.au/json/fantasy/players.json", headers=headers, timeout=30)
        if r.status_code == 200:
            data = r.json()
            print(f"\n✅ Cookie works! Retrieved {len(data)} players.")
        else:
            print(f"\n❌ Cookie test failed: HTTP {r.status_code}")
            print("Make sure you are fully logged in before pressing ENTER.")


if __name__ == "__main__":
    asyncio.run(extract_cookie())
