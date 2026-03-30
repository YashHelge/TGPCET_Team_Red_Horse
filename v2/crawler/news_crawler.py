"""
TradeOS V2 — Financial News Crawler
Customized from sample_crawler.py for stock-specific news scraping.
Uses async httpx with anti-detection, DuckDuckGo search, and content extraction.
"""

import asyncio
import random
import re
import time
import json
import logging
import hashlib
from typing import Optional
from urllib.parse import urlparse
from itertools import cycle

import httpx

logger = logging.getLogger("tradeos.crawler")

# ─── Browser Profiles ──────────────────────────────────────────
PROFILES = [
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
        "lang": "en-US,en;q=0.9",
    },
    {
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 Chrome/123.0.0.0 Safari/537.36",
        "lang": "en-US,en;q=0.9",
    },
    {
        "ua": "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "lang": "en-US,en;q=0.5",
    },
]

_profile_pool = cycle(PROFILES)


def _headers(profile: dict) -> dict:
    return {
        "User-Agent": profile["ua"],
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": profile["lang"],
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


# ─── Content Extraction ────────────────────────────────────────

def extract_article_content(html: str, url: str) -> dict:
    """Extract article content from HTML."""
    # Try trafilatura first
    try:
        import trafilatura
        result = trafilatura.extract(
            html, url=url, include_comments=False,
            include_tables=False, favor_precision=True,
            output_format="json",
        )
        if result:
            data = json.loads(result)
            return {
                "content": data.get("text", ""),
                "title": data.get("title", ""),
                "author": data.get("author"),
                "date": data.get("date"),
            }
    except ImportError:
        pass
    except Exception:
        pass

    # Fallback: regex extraction
    title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
    title = title_match.group(1).strip() if title_match else ""

    # Strip tags
    text = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()[:3000]

    return {"content": text, "title": title, "author": None, "date": None}


# ─── News Search & Scrape ──────────────────────────────────────

async def search_stock_news(
    symbol: str,
    company_name: str = "",
    max_results: int = 10,
) -> list[dict]:
    """Search for stock-specific news using DuckDuckGo."""
    queries = [
        f"{company_name or symbol} stock news today",
        f"{symbol} share price analysis",
        f"{company_name or symbol} earnings results quarterly",
    ]

    all_results = []

    try:
        from ddgs import DDGS
        with DDGS() as ddgs:
            for query in queries[:2]:  # Limit queries
                try:
                    for r in ddgs.text(query, max_results=max_results // 2, safesearch="off"):
                        url = r.get("href", "")
                        # Filter financial news domains
                        domain = urlparse(url).netloc.lower()
                        if any(d in domain for d in [
                            "moneycontrol", "economictimes", "livemint",
                            "reuters", "bloomberg", "cnbc", "financialexpress",
                            "businesstoday", "ndtv", "marketwatch", "yahoo",
                            "seekingalpha", "fool", "investopedia", "barrons",
                        ]):
                            all_results.append({
                                "url": url,
                                "title": r.get("title", ""),
                                "snippet": r.get("body", ""),
                                "source": domain,
                            })
                    await asyncio.sleep(random.uniform(1, 2))
                except Exception as e:
                    logger.debug(f"Search failed for {query}: {e}")
    except ImportError:
        logger.warning("ddgs not available for news search")
    except Exception as e:
        logger.error(f"News search error: {e}")

    # Deduplicate by URL
    seen = set()
    unique = []
    for r in all_results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)

    return unique[:max_results]


async def scrape_articles(
    search_results: list[dict],
    concurrency: int = 3,
) -> list[dict]:
    """Scrape full article content from search results."""
    semaphore = asyncio.Semaphore(concurrency)
    articles = []

    async with httpx.AsyncClient(
        http2=True, verify=True, follow_redirects=True,
        timeout=12,
        limits=httpx.Limits(max_connections=10),
    ) as client:

        async def _scrape(result: dict):
            async with semaphore:
                profile = next(_profile_pool)
                headers = _headers(profile)
                await asyncio.sleep(random.uniform(0.3, 1.5))

                try:
                    resp = await client.get(result["url"], headers=headers)
                    if resp.status_code == 200:
                        extracted = extract_article_content(resp.text, result["url"])
                        if extracted["content"] and len(extracted["content"]) > 50:
                            articles.append({
                                "url": result["url"],
                                "title": extracted["title"] or result["title"],
                                "content": extracted["content"][:2000],
                                "author": extracted["author"],
                                "date": extracted["date"],
                                "source": result.get("source", ""),
                                "snippet": result.get("snippet", ""),
                                "datetime": time.time(),
                            })
                except Exception as e:
                    logger.debug(f"Scrape failed for {result['url']}: {e}")

        await asyncio.gather(*[_scrape(r) for r in search_results])

    return articles


async def get_stock_news(symbol: str, company_name: str = "", max_results: int = 10) -> list[dict]:
    """Full pipeline: search → scrape → extract for a stock."""
    search_results = await search_stock_news(symbol, company_name, max_results)
    if not search_results:
        return []
    articles = await scrape_articles(search_results, concurrency=3)
    return articles
