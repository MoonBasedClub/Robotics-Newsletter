from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CandidateArticleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    discovered_title: str
    discovered_url: str
    source_domain: str
    discovered_at: datetime
    ranking_score: float | None
    rejected_reason: str | None


class SelectedArticleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    canonical_url: str
    title: str
    source_name: str
    author: str | None
    published_at: datetime | None
    category: str
    summary_short: str
    why_it_matters: str
    article_rank: int


class SocialPostRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    body: str
    ordinal: int


class RunSummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scheduled_for: datetime
    completed_at: datetime | None
    status: str
    intro_summary: str | None
    story_count: int
    social_post_count: int


class RunDetailRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scheduled_for: datetime
    started_at: datetime
    completed_at: datetime | None
    status: str
    query_set_version: str
    intro_summary: str | None
    selected_articles: list[SelectedArticleRead]
    social_posts: list[SocialPostRead]
    candidates: list[CandidateArticleRead]


class DataEnvelope(BaseModel):
    data: object


class ListEnvelope(BaseModel):
    data: list[RunSummaryRead]
    meta: dict[str, int]
