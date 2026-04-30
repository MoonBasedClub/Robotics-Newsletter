from datetime import UTC, datetime
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base
from app.domain import ArticleSummary, DiscoveredCandidate, ExtractedArticle, GeneratedPost, RankedArticle
from app.pipeline import _resolve_schedule, run_daily_digest
from app.ranking import rank_and_select


def _build_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def test_resolve_schedule_uses_new_york_9am_across_dst(monkeypatch):
    monkeypatch.setattr(
        "app.pipeline.get_settings",
        lambda: SimpleNamespace(
            scheduler_timezone="America/New_York",
            daily_run_hour=9,
            daily_run_minute=0,
        ),
    )

    march_run = _resolve_schedule("2026-03-10")
    november_run = _resolve_schedule("2026-11-10")

    assert march_run.isoformat() == "2026-03-10T13:00:00+00:00"
    assert november_run.isoformat() == "2026-11-10T14:00:00+00:00"


def test_rank_and_select_dedupes_and_caps_results():
    now = datetime(2026, 4, 29, 13, 0, tzinfo=UTC)
    base_text = "Warehouse robotics is moving into measured deployment at scale. " * 8
    titles = [
        "Warehouse robotics expands into retail fulfillment",
        "Humanoid robots enter a logistics pilot",
        "Warehouse robotics expands into retail fulfillment",
        "Industrial automation startup raises new funding",
        "AI agents move into factory planning software",
        "Robotics policy debate reaches state lawmakers",
        "Machine learning tools improve quality inspection",
        "Autonomous systems startup opens new test site",
        "Foundation model lab ships a smaller model",
        "Robot safety standards get a new industry draft",
    ]
    articles = [
        ExtractedArticle(
            discovered_title=f"Story {index}",
            discovered_url=f"https://example.com/{index}",
            source_domain="example.com",
            discovered_at=now,
            canonical_url=f"https://example.com/canonical-{index if index != 2 else 1}",
            title=titles[index],
            source_name="Example",
            author=None,
            published_at=now,
            cleaned_text=base_text + str(index),
        )
        for index in range(10)
    ]

    selected, rejected = rank_and_select(articles, now=now, limit=8)

    assert len(selected) == 8
    assert any(reason in {"duplicate", "duplicate_title", "below_cutoff"} for _, reason in rejected)
    assert selected[0].ranking_score >= selected[-1].ranking_score


def test_run_daily_digest_persists_completed_run(monkeypatch):
    session = _build_session()
    now = datetime(2026, 4, 29, 13, 0, tzinfo=UTC)
    candidate = DiscoveredCandidate(
        discovered_title="Humanoid robots enter warehouse pilot",
        discovered_url="https://example.com/humanoid-pilot",
        source_domain="example.com",
        discovered_at=now,
    )
    article = ExtractedArticle(
        discovered_title=candidate.discovered_title,
        discovered_url=candidate.discovered_url,
        source_domain=candidate.source_domain,
        discovered_at=now,
        canonical_url=candidate.discovered_url,
        title="Humanoid robots enter warehouse pilot",
        source_name="Example",
        author=None,
        published_at=now,
        cleaned_text="Humanoid robots are moving into warehouse pilots with measurable throughput goals. " * 6,
    )
    ranked = RankedArticle(article=article, ranking_score=9.2, category="Robotics")
    summary = ArticleSummary(
        article=ranked,
        summary_short="Humanoid robots enter warehouse pilot: measurable logistics deployment is becoming the real test.",
        why_it_matters="Shows buyers are evaluating robotics against concrete labor constraints rather than novelty.",
    )

    monkeypatch.setattr("app.pipeline.discover_candidates", lambda now: [candidate])
    monkeypatch.setattr("app.pipeline.extract_and_clean", lambda candidates: ([article], []))
    monkeypatch.setattr("app.pipeline.rank_and_select", lambda articles, now, limit=8: ([ranked], []))
    monkeypatch.setattr("app.pipeline.summarize_articles", lambda ranked_articles: [summary])
    monkeypatch.setattr("app.pipeline.generate_intro_summary", lambda summaries: "A tight robotics-heavy morning.")
    monkeypatch.setattr(
        "app.pipeline.generate_social_posts",
        lambda summaries: [GeneratedPost(body="Robotics is moving from demo to deployment.", ordinal=1)],
    )
    monkeypatch.setattr(
        "app.pipeline.get_settings",
        lambda: SimpleNamespace(
            scheduler_timezone="America/New_York",
            daily_run_hour=9,
            daily_run_minute=0,
        ),
    )

    run_id = run_daily_digest(session, date_override="2026-04-29")

    assert run_id == 1
    run = session.get(models.Run, run_id)
    assert run is not None
    assert run.status == "completed"
    assert len(run.selected_articles) == 1
    assert len(run.social_posts) == 1
    assert run.intro_summary == "A tight robotics-heavy morning."
