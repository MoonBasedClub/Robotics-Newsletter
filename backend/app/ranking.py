from datetime import UTC, datetime
from difflib import SequenceMatcher
import re
from urllib.parse import urlparse

from app.domain import ExtractedArticle, RankedArticle
from app.extraction import cleaned_text_hash


HIGH_SIGNAL_DOMAINS = {
    "techcrunch.com": 1.0,
    "theverge.com": 0.9,
    "venturebeat.com": 0.9,
    "reuters.com": 1.0,
    "www.reuters.com": 1.0,
    "spectrum.ieee.org": 1.0,
    "theinformation.com": 0.8,
    "www.theinformation.com": 0.8,
}


def rank_and_select(
    articles: list[ExtractedArticle],
    now: datetime,
    limit: int = 8,
) -> tuple[list[RankedArticle], list[tuple[ExtractedArticle, str]]]:
    deduped: list[RankedArticle] = []
    rejected: list[tuple[ExtractedArticle, str]] = []
    seen_urls: set[str] = set()
    seen_hashes: set[str] = set()
    ranked_pool: list[RankedArticle] = []

    for article in articles:
        normalized_url = _normalized_url(article.canonical_url)
        text_hash = cleaned_text_hash(article.cleaned_text)
        if normalized_url in seen_urls or text_hash in seen_hashes:
            rejected.append((article, "duplicate"))
            continue

        if any(_similar_title(article.title, existing.article.title) for existing in ranked_pool):
            rejected.append((article, "duplicate_title"))
            continue

        seen_urls.add(normalized_url)
        seen_hashes.add(text_hash)
        ranked_pool.append(
            RankedArticle(
                article=article,
                ranking_score=_score_article(article, now),
                category=_classify_article(article),
            )
        )

    ranked_pool.sort(key=lambda item: item.ranking_score, reverse=True)
    deduped = ranked_pool[:limit]
    rejected.extend((item.article, "below_cutoff") for item in ranked_pool[limit:])
    return deduped, rejected


def _score_article(article: ExtractedArticle, now: datetime) -> float:
    basis = article.published_at or article.discovered_at
    age_hours = max((now.astimezone(UTC) - basis.astimezone(UTC)).total_seconds() / 3600, 0)
    recency_score = max(0.0, 4.0 - age_hours / 8.0)
    topic_score = _topic_score(article)
    source_score = HIGH_SIGNAL_DOMAINS.get(_normalize_domain(article.source_domain), 0.5)
    text_score = min(len(article.cleaned_text) / 2000, 1.2)
    return round(recency_score + topic_score + source_score + text_score, 3)


def _topic_score(article: ExtractedArticle) -> float:
    haystack = f"{article.title} {article.cleaned_text[:1200]}".lower()
    keywords = {
        "robot": 1.6,
        "robots": 1.6,
        "robotics": 1.6,
        "humanoid": 1.6,
        "warehouse": 1.2,
        "automation": 1.1,
        "ai": 1.0,
        "agent": 1.3,
        "model": 0.8,
        "startup": 0.8,
        "funding": 1.1,
        "policy": 1.0,
    }
    return sum(
        weight
        for word, weight in keywords.items()
        if re.search(rf"\b{re.escape(word)}\b", haystack)
    )


def _classify_article(article: ExtractedArticle) -> str:
    haystack = f"{article.title} {article.cleaned_text[:1000]}".lower()
    if "policy" in haystack or "regulation" in haystack:
        return "Policy"
    if "funding" in haystack or "raised" in haystack or "investment" in haystack:
        return "Funding"
    if "research" in haystack or "paper" in haystack:
        return "AI Research"
    if "robot" in haystack or "humanoid" in haystack or "automation" in haystack:
        return "Robotics"
    return "AI Product"


def _normalized_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip("/")
    return f"{_normalize_domain(parsed.netloc)}{path.lower()}"


def _similar_title(left: str, right: str) -> bool:
    return SequenceMatcher(None, left.lower(), right.lower()).ratio() >= 0.93


def _normalize_domain(domain: str) -> str:
    return domain.lower().removeprefix("www.")
