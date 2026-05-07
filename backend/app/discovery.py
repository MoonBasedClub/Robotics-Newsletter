from base64 import urlsafe_b64decode
import binascii
from datetime import UTC, datetime, timedelta
from email.utils import parsedate_to_datetime
import json
import logging
import re
from typing import Callable
from urllib.parse import parse_qs, quote_plus, urlencode, unquote, urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup, Tag

from app.domain import DiscoveredCandidate


logger = logging.getLogger(__name__)
FETCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; news-scraper/0.1)",
}
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
GOOGLE_NEWS_BATCH_ENDPOINT = (
    "https://news.google.com/_/DotsSplashUi/data/batchexecute?rpcids=Fbv4je"
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
    unresolved_google_links = 0

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
        if resolved_url is None:
            if _is_google_news_url(urlparse(link).netloc):
                unresolved_google_links += 1
            continue
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
    if unresolved_google_links:
        logger.warning("skipped %s unresolved Google News RSS links", unresolved_google_links)
    return candidates


def _resolve_google_news_url(
    link: str,
    wrapper_fetcher: Callable[[str], str] | None = None,
    batch_fetcher: Callable[[list[object]], str] | None = None,
) -> str | None:
    parsed = urlparse(link)
    query = parse_qs(parsed.query)
    for key in ("url", "u"):
        if key in query and query[key]:
            return unquote(query[key][0])

    if not _is_google_news_url(parsed.netloc):
        return link

    embedded_url = _decode_google_news_article_url(parsed.path)
    if embedded_url is not None:
        return embedded_url

    article_id = _google_news_article_id(parsed.path)
    if article_id is None:
        return None
    fetch_wrapper = wrapper_fetcher or _default_fetch
    request_payload = _google_news_batch_payload_from_wrapper(
        fetch_wrapper(_google_news_article_url(article_id, parsed.path))
    )
    if request_payload is None:
        return None

    fetch_batch = batch_fetcher or _fetch_google_news_batch_response
    return _extract_google_news_batch_url(fetch_batch(request_payload))


def _decode_google_news_article_url(path: str) -> str | None:
    encoded_id = _google_news_article_id(path)
    if encoded_id is None:
        return None

    padding = "=" * (-len(encoded_id) % 4)
    try:
        decoded = urlsafe_b64decode(encoded_id + padding)
    except (binascii.Error, ValueError):
        return None

    match = re.search(
        rb"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]+",
        decoded,
    )
    if match is None:
        return None

    url = unquote(match.group(0).decode("utf-8", errors="ignore")).rstrip(".,")
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc or _is_google_news_url(parsed.netloc):
        return None
    return url


def _google_news_article_id(path: str) -> str | None:
    encoded_id = path.rstrip("/").split("/")[-1]
    if not encoded_id or not encoded_id.startswith(("CB", "AU_yqL")):
        return None
    return encoded_id


def _google_news_article_url(article_id: str, original_path: str) -> str:
    prefix = "/rss/articles/" if "/rss/articles/" in original_path else "/articles/"
    return f"https://news.google.com{prefix}{article_id}?hl=en-US&gl=US&ceid=US:en"


def _google_news_batch_payload_from_wrapper(html: str) -> list[object] | None:
    soup = BeautifulSoup(html, "html.parser")
    data_node = soup.select_one("c-wiz[data-p]")
    if isinstance(data_node, Tag):
        data_payload = data_node.get("data-p")
        if isinstance(data_payload, str) and data_payload.startswith("%.@."):
            try:
                payload = ["garturlreq", *json.loads(data_payload.removeprefix("%.@."))]
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, list) and len(payload) >= 3:
                return payload[:-6] + payload[-2:]

    params_node = soup.select_one("[data-n-a-id][data-n-a-ts][data-n-a-sg]")
    if not isinstance(params_node, Tag):
        return None

    article_id = params_node.get("data-n-a-id")
    timestamp = params_node.get("data-n-a-ts")
    signature = params_node.get("data-n-a-sg")
    if not isinstance(article_id, str) or not article_id:
        return None
    if not isinstance(timestamp, str) or not timestamp:
        return None
    if not isinstance(signature, str) or not signature:
        return None
    try:
        timestamp_value = int(timestamp)
    except ValueError:
        return None

    return [
        "garturlreq",
        [
            [
                "en-US",
                "US",
                ["FINANCE_TOP_INDICES", "WEB_TEST_1_0_0"],
                None,
                None,
                1,
                1,
                "US:en",
                None,
                180,
                None,
                None,
                None,
                None,
                None,
                0,
                None,
                None,
                [1608992183, 723341000],
            ],
            "en-US",
            "US",
            1,
            [2, 3, 4, 8],
            1,
            0,
            "655000234",
            0,
            0,
            None,
            0,
        ],
        article_id,
        timestamp_value,
        signature,
    ]


def _fetch_google_news_batch_response(request_payload: list[object]) -> str:
    body = urlencode({"f.req": _google_news_batch_payload(request_payload)})
    request = Request(
        GOOGLE_NEWS_BATCH_ENDPOINT,
        data=body.encode("utf-8"),
        headers={
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
            "Referer": "https://news.google.com/",
            **FETCH_HEADERS,
        },
        method="POST",
    )
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="ignore")


def _google_news_batch_payload(request_payload: list[object]) -> str:
    payload = [[["Fbv4je", json.dumps(request_payload, separators=(",", ":")), None, "generic"]]]
    return json.dumps(payload, separators=(",", ":"))


def _extract_google_news_batch_url(response_text: str) -> str | None:
    patterns = (
        r'\["garturlres","(?P<url>https?://.*?)(?=",)',
        r'\\+"garturlres\\+",\\+"(?P<url>https?://.*?)(?=\\+",)',
    )
    for pattern in patterns:
        match = re.search(pattern, response_text)
        if match is None:
            continue
        url = _decode_json_string_fragment(match.group("url")).rstrip(".,")
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc and not _is_google_news_url(parsed.netloc):
            return url
    return None


def _decode_json_string_fragment(value: str) -> str:
    try:
        return json.loads(f'"{value}"')
    except json.JSONDecodeError:
        return value.replace("\\/", "/")


def _is_google_news_url(netloc: str) -> bool:
    domain = netloc.lower().removeprefix("www.")
    return domain == "news.google.com"


def _normalize_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    return f"{parsed.scheme.lower()}://{parsed.netloc.lower()}{path}"


def _default_fetch(url: str) -> str:
    request = Request(url, headers=FETCH_HEADERS)
    with urlopen(request, timeout=20) as response:
        return response.read().decode("utf-8", errors="ignore")
