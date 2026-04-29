from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class DiscoveredCandidate:
    discovered_title: str
    discovered_url: str
    source_domain: str
    discovered_at: datetime


@dataclass(slots=True)
class ExtractedArticle:
    discovered_title: str
    discovered_url: str
    source_domain: str
    discovered_at: datetime
    canonical_url: str
    title: str
    source_name: str
    author: str | None
    published_at: datetime | None
    cleaned_text: str


@dataclass(slots=True)
class RankedArticle:
    article: ExtractedArticle
    ranking_score: float
    category: str


@dataclass(slots=True)
class ArticleSummary:
    article: RankedArticle
    summary_short: str
    why_it_matters: str


@dataclass(slots=True)
class GeneratedPost:
    body: str
    ordinal: int
