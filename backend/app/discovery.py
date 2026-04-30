from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Callable
from urllib.parse import parse_qs, quote_plus, unquote, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from app.domain import DiscoveredCandidate


QUERY_GROUPS = {
    "robotics": [
        "robotics",
        "humanoid robots",
        "autonomous systems",
        "warehouse robotics",
        "industrial robotics",
    ],
    "ai": [
        "artificial intelligence",
        "foundation models",
        "AI agents",
        "machine learning",
        "AI startups",
    ],
}

RSS_TEMPLATE = (
    "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
)


def discover_candidates(
    now: datetime,
    fetcher: Callable[[str], str] | None = None,
    max_age_hours: int = 36,
) -> list[DiscoveredCandidate]:
    fetch = fetcher or _default_fetch
    cutoff = now.astimezone(UTC) - timedelta(hours=max_age_hours)
    candidates: list[DiscoveredCandidate] = []
    seen_urls: set[str] = set()

    for queries in QUERY_GROUPS.values():
        for query in queries:
            try:
                xml_text = fetch(RSS_TEMPLATE.format(query=quote_plus(query)))
                for candidate in _parse_rss(xml_text, cutoff):
                    normalized_url = _normalize_url(candidate.discovered_url)
                    if normalized_url in seen_urls:
                        continue
                    seen_urls.add(normalized_url)
                    candidates.append(candidate)
            except Exception:
                continue

    return candidates


def _parse_rss(xml_text: str, cutoff: datetime) -> list[DiscoveredCandidate]:
    root = ET.fromstring(xml_text)
    items = root.findall(".//item")
    candidates: list[DiscoveredCandidate] = []

    for item in items:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date_raw = (item.findtext("pubDate") or "").strip()
        if not title or not link or not pub_date_raw:
            continue

        try:
            published = parsedate_to_datetime(pub_date_raw).astimezone(UTC)
        except (TypeError, ValueError):
            continue
        if published < cutoff:
            continue

        resolved_url = _resolve_google_news_url(link)
        parsed = urlparse(resolved_url)
        if not parsed.scheme or not parsed.netloc:
            continue
        candidates.append(
            DiscoveredCandidate(
                discovered_title=title,
                discovered_url=resolved_url,
                source_domain=parsed.netloc.lower(),
                discovered_at=published,
            )
        )
    return candidates


def _resolve_google_news_url(link: str) -> str:
    parsed = urlparse(link)
    query = parse_qs(parsed.query)
    for key in ("url", "u"):
        if key in query and query[key]:
            return unquote(query[key][0])
    return link


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{path}"


def _default_fetch(url: str) -> str:
    request = Request(url, headers={"User-Agent": "news-scraper/0.1"})
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="ignore")
