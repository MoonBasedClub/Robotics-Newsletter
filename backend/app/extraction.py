from datetime import datetime
from hashlib import sha256
from typing import Callable
from urllib.parse import urljoin, urlparse
from urllib.request import urlopen

from bs4 import BeautifulSoup

from app.domain import DiscoveredCandidate, ExtractedArticle


def extract_and_clean(
    candidates: list[DiscoveredCandidate],
    fetcher: Callable[[str], str] | None = None,
) -> tuple[list[ExtractedArticle], list[tuple[DiscoveredCandidate, str]]]:
    fetch = fetcher or _default_fetch
    extracted: list[ExtractedArticle] = []
    failures: list[tuple[DiscoveredCandidate, str]] = []

    for candidate in candidates:
        try:
            html = fetch(candidate.discovered_url)
            article = _extract_article(candidate, html)
            if len(article.cleaned_text) < 200:
                failures.append((candidate, "insufficient_text"))
                continue
            extracted.append(article)
        except Exception:
            failures.append((candidate, "extraction_failed"))

    return extracted, failures


def cleaned_text_hash(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def _extract_article(candidate: DiscoveredCandidate, html: str) -> ExtractedArticle:
    soup = BeautifulSoup(html, "html.parser")
    canonical = _first_meta(soup, "link", "rel", "canonical")
    if canonical:
        canonical_url = urljoin(candidate.discovered_url, canonical)
    else:
        og_url = _first_meta_property(soup, "og:url")
        canonical_url = og_url or candidate.discovered_url

    title = (
        _first_meta_property(soup, "og:title")
        or (soup.title.string.strip() if soup.title and soup.title.string else candidate.discovered_title)
    )
    author = _first_meta_name(soup, "author")
    published_raw = (
        _first_meta_property(soup, "article:published_time")
        or _first_meta_name(soup, "pubdate")
    )
    published_at = _parse_datetime(published_raw)
    source_name = urlparse(canonical_url).netloc or candidate.source_domain

    for junk in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
        junk.decompose()

    article_root = soup.find("article")
    content_root = article_root or soup.body or soup
    paragraphs = [
        text.strip()
        for text in (node.get_text(" ", strip=True) for node in content_root.find_all(["p", "li"]))
        if text.strip()
    ]
    cleaned_text = "\n".join(paragraphs)

    return ExtractedArticle(
        discovered_title=candidate.discovered_title,
        discovered_url=candidate.discovered_url,
        source_domain=candidate.source_domain,
        discovered_at=candidate.discovered_at,
        canonical_url=canonical_url,
        title=title,
        source_name=source_name,
        author=author,
        published_at=published_at,
        cleaned_text=cleaned_text,
    )


def _first_meta_property(soup: BeautifulSoup, prop: str) -> str | None:
    tag = soup.find("meta", attrs={"property": prop})
    return tag.get("content", "").strip() if tag else None


def _first_meta_name(soup: BeautifulSoup, name: str) -> str | None:
    tag = soup.find("meta", attrs={"name": name})
    return tag.get("content", "").strip() if tag else None


def _first_meta(soup: BeautifulSoup, tag_name: str, attr_name: str, attr_value: str) -> str | None:
    tag = soup.find(tag_name, attrs={attr_name: attr_value})
    return tag.get("href", "").strip() if tag else None


def _parse_datetime(raw_value: str | None) -> datetime | None:
    if not raw_value:
        return None
    try:
        return datetime.fromisoformat(raw_value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _default_fetch(url: str) -> str:
    with urlopen(url, timeout=20) as response:
        return response.read().decode("utf-8", errors="ignore")
