"""
╔══════════════════════════════════════════════════════════╗
║           ADVANCED WEB INTELLIGENCE SCRAPER              ║
║   Query → Search → Scrape → Extract → Store              ║
╚══════════════════════════════════════════════════════════╝

Scraping Pipeline (3 Tiers, auto-fallback):
  Tier 1  →  curl_cffi   (TLS browser impersonation, fastest)
  Tier 2  →  httpx       (async, randomized fingerprint)
  Tier 3  →  Playwright  (full browser, JS rendering + stealth)

Content Extraction  →  trafilatura (smart boilerplate removal)
Search Engine       →  DuckDuckGo (no API key, best for privacy)
Anti-Detection      →  TLS spoofing, UA rotation, human delays,
                        header correlation, resource blocking
"""

import asyncio
import random
import json
import re
import hashlib
import datetime
import time
from pathlib import Path
from typing import Optional
from itertools import cycle
from dataclasses import dataclass, field, asdict
from urllib.parse import urlparse

# ── Rich UI ─────────────────────────────────────────────────────────
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.prompt import Prompt, IntPrompt
from rich.text import Text
from rich import box
from rich.rule import Rule

# ── Search ────────────────────────────────────────────────────────────
from ddgs import DDGS

# ── HTTP clients ─────────────────────────────────────────────────────
import httpx
from curl_cffi.requests import AsyncSession
import curl_cffi

# ── Content extraction ────────────────────────────────────────────────
import trafilatura
from trafilatura.settings import use_config

# ── Playwright stealth ────────────────────────────────────────────────
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

# ── Retry logic ────────────────────────────────────────────────────────
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

console = Console()

# ─────────────────────────────────────────────────────────────────────
# FINGERPRINT PROFILES  (UA + correlated headers)
# ─────────────────────────────────────────────────────────────────────

BROWSER_PROFILES = [
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "sec_ch_ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "sec_ch_ua_platform": '"Windows"',
        "sec_ch_ua_mobile": "?0",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept_language": "en-US,en;q=0.9",
        "curl_impersonate": "chrome124",
    },
    {
        "ua": "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "sec_ch_ua": '"Google Chrome";v="123", "Not:A-Brand";v="8", "Chromium";v="123"',
        "sec_ch_ua_platform": '"macOS"',
        "sec_ch_ua_mobile": "?0",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "accept_language": "en-US,en;q=0.9",
        "curl_impersonate": "chrome123",
    },
    {
        "ua": "Mozilla/5.0 (X11; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
        "sec_ch_ua": None,
        "sec_ch_ua_platform": None,
        "sec_ch_ua_mobile": None,
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "accept_language": "en-US,en;q=0.5",
        "curl_impersonate": "firefox117",
    },
    {
        "ua": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        "sec_ch_ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Microsoft Edge";v="122"',
        "sec_ch_ua_platform": '"Windows"',
        "sec_ch_ua_mobile": "?0",
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        "accept_language": "en-US,en;q=0.9",
        "curl_impersonate": "chrome110",
    },
]

REFERERS = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://duckduckgo.com/",
    "https://news.ycombinator.com/",
    "https://www.reddit.com/",
]

profile_pool = cycle(BROWSER_PROFILES)

# ─────────────────────────────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────────────────────────────

@dataclass
class ScrapedResult:
    url: str
    domain: str
    title: str
    content: str
    word_count: int
    scraper_tier: str                    # curl_cffi / httpx / playwright
    status_code: Optional[int]
    query: str
    search_rank: int
    scraped_at: str
    language: Optional[str] = None
    author: Optional[str] = None
    publish_date: Optional[str] = None
    tags: list = field(default_factory=list)
    content_hash: str = ""

    def __post_init__(self):
        self.content_hash = hashlib.md5(self.content.encode()).hexdigest()[:12]


@dataclass
class ScrapeStats:
    total: int = 0
    success: int = 0
    tier1_hits: int = 0
    tier2_hits: int = 0
    tier3_hits: int = 0
    blocked: int = 0
    errors: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def elapsed(self) -> str:
        return f"{time.time() - self.start_time:.1f}s"

    @property
    def success_rate(self) -> str:
        if self.total == 0:
            return "0%"
        return f"{(self.success / self.total) * 100:.0f}%"


# ─────────────────────────────────────────────────────────────────────
# TRAFILATURA CONFIG
# ─────────────────────────────────────────────────────────────────────

traf_config = use_config()
traf_config.set("DEFAULT", "EXTRACTION_TIMEOUT", "10")
traf_config.set("DEFAULT", "MIN_EXTRACTED_SIZE", "100")


def extract_content(html: str, url: str) -> dict:
    """Smart content extraction stripping ads, navbars, footers."""
    try:
        result = trafilatura.extract(
            html,
            url=url,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            favor_precision=True,
            config=traf_config,
            output_format="json",
        )
        if result:
            data = json.loads(result)
            return {
                "content": data.get("text", ""),
                "title": data.get("title", ""),
                "author": data.get("author"),
                "date": data.get("date"),
                "language": data.get("language"),
                "tags": data.get("tags", []) or [],
            }
    except Exception:
        pass

    # Fallback: raw trafilatura text
    try:
        text = trafilatura.extract(html, url=url, include_comments=False)
        return {"content": text or "", "title": "", "author": None, "date": None, "language": None, "tags": []}
    except Exception:
        return {"content": "", "title": "", "author": None, "date": None, "language": None, "tags": []}


def build_headers(profile: dict, referer: Optional[str] = None) -> dict:
    headers = {
        "User-Agent": profile["ua"],
        "Accept": profile["accept"],
        "Accept-Language": profile["accept_language"],
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }
    if referer:
        headers["Referer"] = referer
    if profile.get("sec_ch_ua"):
        headers["sec-ch-ua"] = profile["sec_ch_ua"]
        headers["sec-ch-ua-mobile"] = profile["sec_ch_ua_mobile"]
        headers["sec-ch-ua-platform"] = profile["sec_ch_ua_platform"]
        headers["Sec-Fetch-Dest"] = "document"
        headers["Sec-Fetch-Mode"] = "navigate"
        headers["Sec-Fetch-Site"] = "cross-site" if referer else "none"
        headers["Sec-Fetch-User"] = "?1"
    return headers


# ─────────────────────────────────────────────────────────────────────
# TIER 1 — curl_cffi (TLS browser fingerprint impersonation)
# ─────────────────────────────────────────────────────────────────────

async def tier1_curl(url: str, profile: dict) -> Optional[tuple[str, int]]:
    """Fastest tier: TLS fingerprint spoofing via curl_cffi."""
    try:
        async with AsyncSession(impersonate=profile["curl_impersonate"]) as session:
            headers = build_headers(profile, random.choice(REFERERS))
            resp = await session.get(
                url,
                headers=headers,
                timeout=20,
                allow_redirects=True,
            )
            if resp.status_code < 400:
                return resp.text, resp.status_code
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────────────────
# TIER 2 — httpx async (fast, randomized headers)
# ─────────────────────────────────────────────────────────────────────

async def tier2_httpx(url: str, profile: dict) -> Optional[tuple[str, int]]:
    """Second tier: async httpx with header randomization."""
    try:
        headers = build_headers(profile, random.choice(REFERERS))
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        async with httpx.AsyncClient(
            headers=headers,
            follow_redirects=True,
            timeout=25,
            limits=limits,
            verify=False,
            http2=True,
        ) as client:
            resp = await client.get(url)
            if resp.status_code < 400:
                return resp.text, resp.status_code
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────────────────────────────
# TIER 3 — Playwright stealth (full browser, JS rendering)
# ─────────────────────────────────────────────────────────────────────

stealth_instance = Stealth()


async def block_non_essential(route):
    """Block heavy resources; allow CSS/JS for anti-bot bypass."""
    blocked = {"image", "font", "media"}
    if route.request.resource_type in blocked:
        await route.abort()
    else:
        await route.continue_()


async def tier3_playwright(url: str, profile: dict, browser) -> Optional[tuple[str, int]]:
    """Third tier: full browser with stealth patches."""
    context = await browser.new_context(
        user_agent=profile["ua"],
        viewport={"width": random.choice([1280, 1366, 1440, 1920]),
                  "height": random.choice([768, 800, 900, 1080])},
        locale="en-US",
        timezone_id=random.choice(["America/New_York", "America/Los_Angeles", "Europe/London"]),
        extra_http_headers={
            "Accept-Language": profile["accept_language"],
            "Referer": random.choice(REFERERS),
            "Upgrade-Insecure-Requests": "1",
        },
        java_script_enabled=True,
        ignore_https_errors=True,
    )

    page = await context.new_page()
    status_code = None

    try:
        await page.route("**/*", block_non_essential)

        # Human-like: jitter before request
        await asyncio.sleep(random.uniform(1.0, 2.5))

        try:
            async with stealth_instance.use_async(page):
                resp = await page.goto(url, timeout=45000, wait_until="domcontentloaded")
                status_code = resp.status if resp else None
        except Exception:
            resp = await page.goto(url, timeout=45000, wait_until="domcontentloaded")
            status_code = resp.status if resp else None

        if status_code and status_code >= 400:
            return None

        # Simulate human scroll
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.3)")
        await asyncio.sleep(random.uniform(0.8, 2.0))

        html = await page.content()
        return html, status_code or 200

    except Exception:
        return None
    finally:
        await page.close()
        await context.close()


# ─────────────────────────────────────────────────────────────────────
# SMART SCRAPING ENGINE  (cascading tiers)
# ─────────────────────────────────────────────────────────────────────

async def smart_scrape(url: str, query: str, rank: int, browser, stats: ScrapeStats) -> Optional[ScrapedResult]:
    stats.total += 1
    profile = next(profile_pool)
    domain = urlparse(url).netloc.replace("www.", "")

    # ── Tier 1: curl_cffi ──────────────────────────────────────────
    result = await tier1_curl(url, profile)
    tier_used = "curl_cffi"

    # ── Tier 2: httpx ──────────────────────────────────────────────
    if not result:
        await asyncio.sleep(random.uniform(0.5, 1.5))
        result = await tier2_httpx(url, profile)
        tier_used = "httpx"

    # ── Tier 3: Playwright ─────────────────────────────────────────
    if not result:
        await asyncio.sleep(random.uniform(1.0, 2.5))
        result = await tier3_playwright(url, profile, browser)
        tier_used = "playwright"

    if not result:
        stats.blocked += 1
        stats.errors += 1
        return None

    html, status_code = result

    # Track tier hits
    if tier_used == "curl_cffi":
        stats.tier1_hits += 1
    elif tier_used == "httpx":
        stats.tier2_hits += 1
    else:
        stats.tier3_hits += 1

    # ── Content Extraction ─────────────────────────────────────────
    extracted = extract_content(html, url)
    content = extracted["content"].strip()

    if not content or len(content) < 80:
        # Fallback: raw body text via regex strip
        content = re.sub(r"<[^>]+>", " ", html)
        content = re.sub(r"\s+", " ", content).strip()
        content = content[:3000]

    if not content:
        stats.errors += 1
        return None

    title = extracted["title"] or domain

    stats.success += 1
    return ScrapedResult(
        url=url,
        domain=domain,
        title=title,
        content=content,
        word_count=len(content.split()),
        scraper_tier=tier_used,
        status_code=status_code,
        query=query,
        search_rank=rank,
        scraped_at=datetime.datetime.now().isoformat(),
        language=extracted.get("language"),
        author=extracted.get("author"),
        publish_date=extracted.get("date"),
        tags=extracted.get("tags", []),
    )


# ─────────────────────────────────────────────────────────────────────
# SEARCH ENGINE — DuckDuckGo
# ─────────────────────────────────────────────────────────────────────

def search_ddgs(query: str, max_results: int = 10) -> list[dict]:
    """Search DuckDuckGo and return structured results."""
    results = []
    try:
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results, safesearch="off"):
                results.append({
                    "url": r.get("href", ""),
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                })
    except Exception as e:
        console.print(f"[red]Search error: {e}[/red]")
    return results


# ─────────────────────────────────────────────────────────────────────
# OUTPUT MANAGER
# ─────────────────────────────────────────────────────────────────────

def save_results(results: list[ScrapedResult], query: str, output_dir: Path) -> tuple[Path, Path]:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_query = re.sub(r"[^\w\s-]", "", query).strip().replace(" ", "_")[:40]
    base = f"scrape_{safe_query}_{ts}"

    # ── JSON ────────────────────────────────────────────────────────
    json_path = output_dir / f"{base}.json"
    json_data = {
        "metadata": {
            "query": query,
            "total_results": len(results),
            "scraped_at": ts,
            "generator": "AdvancedScraper v2.0",
        },
        "results": [asdict(r) for r in results],
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    # ── TXT ─────────────────────────────────────────────────────────
    txt_path = output_dir / f"{base}.txt"
    separator = "═" * 80

    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"{'═' * 80}\n")
        f.write(f"  ADVANCED WEB INTELLIGENCE SCRAPER — RESULTS\n")
        f.write(f"{'═' * 80}\n")
        f.write(f"  Query       : {query}\n")
        f.write(f"  Total Found : {len(results)}\n")
        f.write(f"  Scraped At  : {ts}\n")
        f.write(f"{'═' * 80}\n\n")

        for idx, r in enumerate(results, 1):
            f.write(f"\n{'─' * 80}\n")
            f.write(f"  [{idx:02d}] {r.title}\n")
            f.write(f"{'─' * 80}\n")
            f.write(f"  URL         : {r.url}\n")
            f.write(f"  Domain      : {r.domain}\n")
            f.write(f"  Search Rank : #{r.search_rank}\n")
            f.write(f"  Scraper     : {r.scraper_tier}\n")
            f.write(f"  Status Code : {r.status_code}\n")
            f.write(f"  Word Count  : {r.word_count:,}\n")
            f.write(f"  Language    : {r.language or 'unknown'}\n")
            if r.author:
                f.write(f"  Author      : {r.author}\n")
            if r.publish_date:
                f.write(f"  Published   : {r.publish_date}\n")
            if r.tags:
                f.write(f"  Tags        : {', '.join(r.tags[:8])}\n")
            f.write(f"  Hash        : {r.content_hash}\n")
            f.write(f"  Scraped At  : {r.scraped_at}\n")
            f.write(f"\n  ── CONTENT ──\n\n")
            # Wrap content at 78 chars
            words = r.content.split()
            line, lines = [], []
            for word in words:
                line.append(word)
                if len(" ".join(line)) > 76:
                    lines.append("  " + " ".join(line))
                    line = []
            if line:
                lines.append("  " + " ".join(line))
            f.write("\n".join(lines))
            f.write(f"\n\n{separator}\n")

    return json_path, txt_path


# ─────────────────────────────────────────────────────────────────────
# UI HELPERS
# ─────────────────────────────────────────────────────────────────────

def print_banner():
    console.print()
    console.print(Panel(
        Text.from_markup(
            "[bold cyan]ADVANCED WEB INTELLIGENCE SCRAPER[/bold cyan]\n"
            "[dim]Query → Search → Scrape → Extract → Store[/dim]\n\n"
            "[yellow]Tier 1[/yellow] [dim]curl_cffi   — TLS browser impersonation[/dim]\n"
            "[yellow]Tier 2[/yellow] [dim]httpx       — Async HTTP/2 client[/dim]\n"
            "[yellow]Tier 3[/yellow] [dim]Playwright  — Full browser + stealth[/dim]\n\n"
            "[dim]Content extraction via trafilatura[/dim]"
        ),
        border_style="cyan",
        padding=(1, 4),
    ))
    console.print()


def print_search_results(search_hits: list[dict]):
    table = Table(
        title="Search Results",
        box=box.ROUNDED,
        border_style="blue",
        header_style="bold blue",
        show_lines=False,
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Title", style="bold white", max_width=45)
    table.add_column("Domain", style="cyan", max_width=30)
    table.add_column("Snippet", style="dim", max_width=50)

    for i, r in enumerate(search_hits, 1):
        domain = urlparse(r["url"]).netloc.replace("www.", "")
        table.add_row(
            str(i),
            r["title"][:44],
            domain[:29],
            r["snippet"][:49],
        )
    console.print(table)
    console.print()


def print_stats(stats: ScrapeStats, results: list[ScrapedResult]):
    table = Table(
        title="Scrape Summary",
        box=box.SIMPLE_HEAVY,
        border_style="green",
        header_style="bold green",
    )
    table.add_column("Metric", style="bold white")
    table.add_column("Value", style="green")

    table.add_row("Total URLs", str(stats.total))
    table.add_row("Successful", f"[bold green]{stats.success}[/bold green]")
    table.add_row("Success Rate", stats.success_rate)
    table.add_row("Blocked / Errors", f"[red]{stats.blocked}[/red]")
    table.add_row("Tier 1 (curl_cffi)", str(stats.tier1_hits))
    table.add_row("Tier 2 (httpx)", str(stats.tier2_hits))
    table.add_row("Tier 3 (Playwright)", str(stats.tier3_hits))
    table.add_row("Elapsed", stats.elapsed)

    if results:
        avg_words = sum(r.word_count for r in results) // len(results)
        table.add_row("Avg Word Count", f"{avg_words:,}")

    console.print(table)


# ─────────────────────────────────────────────────────────────────────
# MAIN ENGINE
# ─────────────────────────────────────────────────────────────────────

async def run_scraper(query: str, max_results: int, concurrency: int):
    stats = ScrapeStats()
    output_dir = Path("scraper_output")
    output_dir.mkdir(exist_ok=True)

    # ── Step 1: Search ──────────────────────────────────────────────
    console.print(Rule("[bold blue]Step 1 — Searching DuckDuckGo[/bold blue]"))
    console.print(f"  [cyan]Query:[/cyan] {query}")
    console.print(f"  [cyan]Max results:[/cyan] {max_results}\n")

    with console.status("[bold cyan]Searching DuckDuckGo...[/bold cyan]"):
        search_hits = search_ddgs(query, max_results=max_results)

    if not search_hits:
        console.print("[red]No search results found. Try a different query.[/red]")
        return

    console.print(f"  [green]✓[/green] Found {len(search_hits)} URLs\n")
    print_search_results(search_hits)

    # ── Step 2: Scrape ──────────────────────────────────────────────
    console.print(Rule("[bold blue]Step 2 — Scraping URLs[/bold blue]"))

    scraped_results: list[ScrapedResult] = []
    semaphore = asyncio.Semaphore(concurrency)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ]
        )

        async def bounded_scrape(url: str, rank: int):
            async with semaphore:
                result = await smart_scrape(url, query, rank, browser, stats)
                if result:
                    scraped_results.append(result)
                    console.print(
                        f"  [green]✓[/green] [{result.scraper_tier:>10}] "
                        f"[bold]{result.domain:<30}[/bold] "
                        f"[dim]{result.word_count:>5} words[/dim]"
                    )
                else:
                    domain = urlparse(url).netloc.replace("www.", "")
                    console.print(f"  [red]✗[/red] [dim]{domain}[/dim] — skipped")

        tasks = [bounded_scrape(hit["url"], i + 1) for i, hit in enumerate(search_hits)]
        await asyncio.gather(*tasks)

        await browser.close()

    # ── Step 3: Save ────────────────────────────────────────────────
    console.print()
    console.print(Rule("[bold blue]Step 3 — Saving Results[/bold blue]"))

    if scraped_results:
        # Sort by search rank
        scraped_results.sort(key=lambda r: r.search_rank)
        json_path, txt_path = save_results(scraped_results, query, output_dir)
        console.print(f"\n  [green]✓[/green] JSON  →  [cyan]{json_path}[/cyan]")
        console.print(f"  [green]✓[/green] TXT   →  [cyan]{txt_path}[/cyan]\n")
    else:
        console.print("[red]No results to save.[/red]")

    # ── Stats ────────────────────────────────────────────────────────
    console.print()
    print_stats(stats, scraped_results)


# ─────────────────────────────────────────────────────────────────────
# INTERACTIVE ENTRY POINT
# ─────────────────────────────────────────────────────────────────────

def main():
    print_banner()

    console.print("[bold]Configure your scrape session:[/bold]\n")

    query = Prompt.ask("  [cyan]Enter your search query[/cyan]").strip()
    if not query:
        console.print("[red]Query cannot be empty.[/red]")
        return

    max_results = IntPrompt.ask(
        "  [cyan]Number of URLs to scrape[/cyan]",
        default=8,
        show_default=True,
    )
    max_results = max(1, min(max_results, 20))

    concurrency = IntPrompt.ask(
        "  [cyan]Concurrent scrapers[/cyan] [dim](recommended: 3-5)[/dim]",
        default=4,
        show_default=True,
    )
    concurrency = max(1, min(concurrency, 8))

    console.print()
    console.print(Rule("[dim]Starting scrape session[/dim]"))
    console.print()

    asyncio.run(run_scraper(query, max_results, concurrency))


if __name__ == "__main__":
    main()