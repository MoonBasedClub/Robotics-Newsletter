from datetime import UTC, datetime

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.api as api_module
from app import models
from app.api import app, get_db
from app.database import Base


def _seed_session():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = SessionLocal()

    run = models.Run(
        scheduled_for=datetime(2026, 4, 29, 13, 0, tzinfo=UTC),
        started_at=datetime(2026, 4, 29, 13, 0, tzinfo=UTC),
        completed_at=datetime(2026, 4, 29, 13, 5, tzinfo=UTC),
        status="completed",
        query_set_version="v1",
        intro_summary="A concise morning brief.",
    )
    session.add(run)
    session.flush()
    session.add(
        models.CandidateArticle(
            run_id=run.id,
            discovered_title="AI agents land in operations software",
            discovered_url="https://example.com/agents",
            source_domain="example.com",
            discovered_at=datetime(2026, 4, 29, 12, 30, tzinfo=UTC),
            ranking_score=8.1,
            rejected_reason=None,
        )
    )
    session.add(
        models.SelectedArticle(
            run_id=run.id,
            canonical_url="https://example.com/agents",
            title="AI agents land in operations software",
            source_name="Example",
            author=None,
            published_at=datetime(2026, 4, 29, 12, 30, tzinfo=UTC),
            cleaned_text_hash="abc123",
            category="AI Product",
            summary_short="Operational AI products are converging on workflow execution.",
            why_it_matters="Signals buyers want AI that acts inside existing operating systems.",
            article_rank=1,
        )
    )
    session.add(models.SocialPost(run_id=run.id, body="AI agents are shipping into operational workflows.", ordinal=1))
    session.commit()
    return engine, session


def test_runs_api_returns_latest_and_archive():
    engine, session = _seed_session()

    def override_get_db():
        try:
            yield session
        finally:
            pass

    api_module.engine = engine
    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    runs_response = client.get("/api/runs")
    latest_response = client.get("/api/runs/latest")
    detail_response = client.get("/api/runs/1")

    assert runs_response.status_code == 200
    assert runs_response.json()["meta"]["total"] == 1

    assert latest_response.status_code == 200
    latest_data = latest_response.json()["data"]
    assert latest_data["status"] == "completed"
    assert len(latest_data["selected_articles"]) == 1

    assert detail_response.status_code == 200
    assert detail_response.json()["data"]["social_posts"][0]["ordinal"] == 1

    app.dependency_overrides.clear()
