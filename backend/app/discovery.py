from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
from typing import Callable
from urllib.parse import parse_qs, unquote, urlparse
from urllib.request import urlopen
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

    for queries in QUERY_GROUPS.values():
        for query in queries:
            try:
                xml_text = fetch(RSS_TEMPLATE.format(query=query.replace(" ", "+")))
                candidates.extend(_parse_rss(xml_text, cutoff))
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

        published = parsedate_to_datetime(pub_date_raw).astimezone(UTC)
        if published < cutoff:
            continue

        resolved_url = _resolve_google_news_url(link)
        parsed = urlparse(resolved_url)
        candidates.append(
            DiscoveredCandidate(
                discovered_title=title,
                discovered_url=resolved_url,
                source_domain=parsed.netloc,
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


def _default_fetch(url: str) -> str:
    with urlopen(url, timeout=20) as response:
        return response.read().decode("utf-8", errors="ignore")
