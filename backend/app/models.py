from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    query_set_version: Mapped[str] = mapped_column(String(64), default="v1")
    intro_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    candidates: Mapped[list["CandidateArticle"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="CandidateArticle.id",
    )
    selected_articles: Mapped[list["SelectedArticle"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="SelectedArticle.article_rank",
    )
    social_posts: Mapped[list["SocialPost"]] = relationship(
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="SocialPost.ordinal",
    )


class CandidateArticle(Base):
    __tablename__ = "candidate_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), index=True)
    discovered_title: Mapped[str] = mapped_column(String(512))
    discovered_url: Mapped[str] = mapped_column(Text)
    source_domain: Mapped[str] = mapped_column(String(255))
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ranking_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    rejected_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    run: Mapped[Run] = relationship(back_populates="candidates")


class SelectedArticle(Base):
    __tablename__ = "selected_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), index=True)
    canonical_url: Mapped[str] = mapped_column(Text)
    title: Mapped[str] = mapped_column(String(512))
    source_name: Mapped[str] = mapped_column(String(255))
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cleaned_text_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    summary_short: Mapped[str] = mapped_column(Text)
    why_it_matters: Mapped[str] = mapped_column(Text)
    article_rank: Mapped[int] = mapped_column(Integer)

    run: Mapped[Run] = relationship(back_populates="selected_articles")


class SocialPost(Base):
    __tablename__ = "social_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("runs.id", ondelete="CASCADE"), index=True)
    body: Mapped[str] = mapped_column(Text)
    ordinal: Mapped[int] = mapped_column(Integer)

    run: Mapped[Run] = relationship(back_populates="social_posts")
