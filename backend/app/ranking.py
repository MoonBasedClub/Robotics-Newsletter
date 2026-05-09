from datetime import UTC, datetime
from difflib import SequenceMatcher
import re
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

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
    rejected: list[tuple[ExtractedArticle, str]] = []
    seen_urls: set[str] = set()
    seen_hashes: set[str] = set()
    seen_fingerprints: list[set[str]] = []
    ranked_pool = [
        RankedArticle(
            article=article,
            ranking_score=_score_article(article, now),
            category=_classify_article(article),
        )
        for article in articles
    ]
    ranked_pool.sort(key=lambda item: item.ranking_score, reverse=True)

    deduped_pool: list[RankedArticle] = []
    for ranked_article in ranked_pool:
        article = ranked_article.article
        normalized_url = _normalized_url(article.canonical_url)
        text_hash = cleaned_text_hash(article.cleaned_text)
        fingerprint = _text_fingerprint(article.cleaned_text)

        if normalized_url in seen_urls:
            rejected.append((article, "duplicate_url"))
            continue

        if text_hash in seen_hashes or any(_similar_text(fingerprint, seen) for seen in seen_fingerprints):
            rejected.append((article, "duplicate_text"))
            continue

        if any(_similar_title(article.title, existing.article.title) for existing in deduped_pool):
            rejected.append((article, "duplicate_title"))
            continue

        seen_urls.add(normalized_url)
        seen_hashes.add(text_hash)
        seen_fingerprints.append(fingerprint)
        deduped_pool.append(ranked_article)

    deduped = deduped_pool[:limit]
    rejected.extend((item.article, "below_cutoff") for item in deduped_pool[limit:])
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
    query = urlencode(
        [
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if not _is_tracking_param(key)
        ],
        doseq=True,
    )
    path = parsed.path.rstrip("/")
    return urlunparse(
        (
            "",
            _normalize_domain(parsed.netloc),
            path.lower(),
            "",
            query,
            "",
        )
    )


def _similar_title(left: str, right: str) -> bool:
    return SequenceMatcher(None, _normalize_title(left), _normalize_title(right)).ratio() >= 0.90


def _normalize_domain(domain: str) -> str:
    return domain.lower().removeprefix("www.")


def _is_tracking_param(name: str) -> bool:
    lowered = name.lower()
    return lowered.startswith("utm_") or lowered in {
        "fbclid",
        "gclid",
        "mc_cid",
        "mc_eid",
        "oc",
    }


def _normalize_title(title: str) -> str:
    title_without_source = re.split(r"\s[-|]\s", title, maxsplit=1)[0]
    normalized = re.sub(r"[^a-z0-9\s]", " ", title_without_source.lower())
    return " ".join(normalized.split())


def _text_fingerprint(text: str, shingle_size: int = 5) -> set[str]:
    tokens = [
        token
        for token in re.findall(r"[a-z0-9]+", text.lower())
        if len(token) > 2
    ]
    if len(tokens) < shingle_size:
        return set(tokens)
    return {
        " ".join(tokens[index : index + shingle_size])
        for index in range(len(tokens) - shingle_size + 1)
    }


def _similar_text(left: set[str], right: set[str]) -> bool:
    if not left or not right:
        return False
    overlap = len(left & right)
    union = len(left | right)
    return overlap / union >= 0.72
