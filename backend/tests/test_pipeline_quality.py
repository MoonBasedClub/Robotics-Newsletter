from base64 import urlsafe_b64encode
from datetime import UTC, datetime, timedelta
from html import escape as escape_attr
import json
from types import SimpleNamespace
from xml.sax.saxutils import escape as escape_xml

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import models
from app.database import Base
from app.discovery import _resolve_google_news_url, discover_candidates
from app.domain import DiscoveredCandidate, ExtractedArticle
from app.extraction import extract_and_clean
from app.pipeline import run_daily_digest
from app.ranking import rank_and_select


def _build_session() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)()


def _candidate(url: str, title: str = "Warehouse robotics expands") -> DiscoveredCandidate:
    return DiscoveredCandidate(
        discovered_title=title,
        discovered_url=url,
        source_domain="example.com",
        discovered_at=datetime(2026, 4, 29, 13, 0, tzinfo=UTC),
    )


def _article(
    title: str,
    text: str,
    url: str = "https://example.com/story",
    source_domain: str = "example.com",
) -> ExtractedArticle:
    return ExtractedArticle(
        discovered_title=title,
        discovered_url=url,
        source_domain=source_domain,
        discovered_at=datetime(2026, 4, 29, 13, 0, tzinfo=UTC),
        canonical_url=url,
        title=title,
        source_name=source_domain,
        author=None,
        published_at=datetime(2026, 4, 29, 12, 0, tzinfo=UTC),
        cleaned_text=text,
    )


def _google_news_article_link(article_url: str) -> str:
    encoded = urlsafe_b64encode(
        b"\x08\x13" + article_url.encode("utf-8") + b"\xd2\x01\x00"
    ).decode("ascii").rstrip("=")
    return f"https://news.google.com/rss/articles/{encoded}?oc=5"


def _google_news_wrapper_html(article_id: str) -> str:
    data_payload = "%.@." + json.dumps(
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
                None,
                None,
                None,
                None,
                None,
                None,
                False,
                5,
            ],
            "en-US",
            "US",
            True,
            [3, 5, 9, 19],
            1,
            True,
            "910314302",
            None,
            None,
            None,
            False,
            article_id,
            1,
            1,
            None,
            False,
            1778120025,
            "test-signature",
        ],
        separators=(",", ":"),
    )
    return f'<html><body><c-wiz data-p="{escape_attr(data_payload)}"></c-wiz></body></html>'


def test_discovery_filters_old_invalid_and_duplicate_rss_items():
    now = datetime(2026, 4, 29, 13, 0, tzinfo=UTC)
    fresh_date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
    old_date = (now - timedelta(hours=48)).strftime("%a, %d %b %Y %H:%M:%S GMT")
    xml = f"""
    <rss><channel>
      <item>
        <title>Robotics startup expands pilots</title>
        <link>https://news.google.com/rss/articles/example?url=https%3A%2F%2Fexample.com%2Fstory%3Futm_source%3Drss</link>
        <pubDate>{fresh_date}</pubDate>
      </item>
      <item>
        <title>Duplicate robotics startup expands pilots</title>
        <link>https://example.com/story?utm_campaign=mirror</link>
        <pubDate>{fresh_date}</pubDate>
      </item>
      <item>
        <title>Old AI story</title>
        <link>https://example.com/old</link>
        <pubDate>{old_date}</pubDate>
      </item>
      <item>
        <title>Bad date story</title>
        <link>https://example.com/bad-date</link>
        <pubDate>not a date</pubDate>
      </item>
    </channel></rss>
    """

    candidates = discover_candidates(now=now, fetcher=lambda _: xml)

    assert len(candidates) == 1
    assert candidates[0].discovered_url == "https://example.com/story?utm_source=rss"
    assert candidates[0].source_domain == "example.com"


def test_discovery_resolves_encoded_google_news_article_links():
    now = datetime(2026, 4, 29, 13, 0, tzinfo=UTC)
    fresh_date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
    article_url = "https://robotics.example.com/news/humanoid-pilot?utm_source=google-news"
    google_link = escape_xml(_google_news_article_link(article_url))
    xml = f"""
    <rss><channel>
      <item>
        <title>Humanoid robots enter warehouse pilot</title>
        <link>{google_link}</link>
        <pubDate>{fresh_date}</pubDate>
      </item>
    </channel></rss>
    """

    candidates = discover_candidates(now=now, fetcher=lambda _: xml)

    assert len(candidates) == 1
    assert candidates[0].discovered_url == article_url
    assert candidates[0].source_domain == "robotics.example.com"


def test_discovery_skips_unresolvable_google_news_article_links():
    now = datetime(2026, 4, 29, 13, 0, tzinfo=UTC)
    fresh_date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
    xml = f"""
    <rss><channel>
      <item>
        <title>Google wrapper without original URL</title>
        <link>https://news.google.com/rss/articles/not-a-decodable-id?oc=5</link>
        <pubDate>{fresh_date}</pubDate>
      </item>
    </channel></rss>
    """

    candidates = discover_candidates(now=now, fetcher=lambda _: xml)

    assert candidates == []


def test_google_news_resolver_uses_batch_fallback_for_opaque_article_ids():
    article_url = "https://example.com/robotics/story?utm_source=google-news"
    article_id = "CBMopaqueArticleId"
    link = f"https://news.google.com/rss/articles/{article_id}?oc=5"
    response = (
        ")]}'\n"
        f'[[["wrb.fr","Fbv4je","[\\"garturlres\\",\\"{article_url}\\",1]",'
        'null,null,null,"generic"]]]'
    )

    resolved = _resolve_google_news_url(
        link,
        wrapper_fetcher=lambda _: _google_news_wrapper_html(article_id),
        batch_fetcher=lambda _: response,
    )

    assert resolved == article_url


def test_discovery_dedupes_old_and_encoded_google_news_wrappers():
    now = datetime(2026, 4, 29, 13, 0, tzinfo=UTC)
    fresh_date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")
    article_url = "https://example.com/story"
    google_link = escape_xml(_google_news_article_link(article_url))
    xml = f"""
    <rss><channel>
      <item>
        <title>Robotics pilot original wrapper</title>
        <link>https://news.google.com/rss/articles/example?url=https%3A%2F%2Fexample.com%2Fstory%3Futm_source%3Drss</link>
        <pubDate>{fresh_date}</pubDate>
      </item>
      <item>
        <title>Robotics pilot encoded wrapper</title>
        <link>{google_link}</link>
        <pubDate>{fresh_date}</pubDate>
      </item>
    </channel></rss>
    """

    candidates = discover_candidates(now=now, fetcher=lambda _: xml)

    assert len(candidates) == 1
    assert candidates[0].source_domain == "example.com"


def test_extraction_normalizes_text_metadata_and_dates():
    html = """
    <html>
      <head>
        <link rel="canonical" href="/canonical-story" />
        <meta property="og:title" content="  Humanoid   robots enter warehouses  " />
        <meta name="author" content="Jane Reporter" />
        <meta name="pubdate" content="Wed, 29 Apr 2026 12:30:00 GMT" />
      </head>
      <body>
        <header>Navigation</header>
        <article>
          <p>Humanoid robots are moving into warehouse pilots with measurable throughput goals.</p>
          <p>Humanoid robots are moving into warehouse pilots with measurable throughput goals.</p>
          <p>Operators are testing whether these systems can handle repetitive movement safely and reliably.</p>
          <p>Deployment teams are measuring utilization, failure recovery, and labor fit before wider rollouts.</p>
        </article>
      </body>
    </html>
    """

    extracted, failures = extract_and_clean(
        [_candidate("https://example.com/articles/original")],
        fetcher=lambda _: html,
    )

    assert failures == []
    assert len(extracted) == 1
    article = extracted[0]
    assert article.canonical_url == "https://example.com/canonical-story"
    assert article.title == "Humanoid robots enter warehouses"
    assert article.author == "Jane Reporter"
    assert article.published_at == datetime(2026, 4, 29, 12, 30, tzinfo=UTC)
    assert article.cleaned_text.count("Humanoid robots are moving") == 1


def test_ranking_uses_word_boundaries_for_ai_signal():
    now = datetime(2026, 4, 29, 13, 0, tzinfo=UTC)
    noisy_text = "The chair said this market update was mainly about enterprise budgets. " * 8
    relevant_text = "AI agents are moving into enterprise operations with measurable workflow gains. " * 8

    selected, _ = rank_and_select(
        [
            _article("Enterprise chair comments on budgets", noisy_text, "https://example.com/noisy"),
            _article("AI agents land in operations", relevant_text, "https://example.com/relevant"),
        ],
        now=now,
        limit=2,
    )

    assert selected[0].article.title == "AI agents land in operations"
    assert selected[0].ranking_score > selected[1].ranking_score


def test_pipeline_marks_partial_run_and_extraction_failure(monkeypatch):
    session = _build_session()
    candidate = _candidate("https://example.com/no-body", "AI story with no body")

    monkeypatch.setattr("app.pipeline.discover_candidates", lambda now: [candidate])
    monkeypatch.setattr("app.pipeline.extract_and_clean", lambda candidates: ([], [(candidate, "insufficient_text")]))
    monkeypatch.setattr("app.pipeline.rank_and_select", lambda articles, now, limit=8: ([], []))
    monkeypatch.setattr("app.pipeline.summarize_articles", lambda ranked_articles: [])
    monkeypatch.setattr(
        "app.pipeline.get_settings",
        lambda: SimpleNamespace(
            scheduler_timezone="America/New_York",
            daily_run_hour=9,
            daily_run_minute=0,
        ),
    )

    run_id = run_daily_digest(session, date_override="2026-04-29")

    run = session.get(models.Run, run_id)
    assert run is not None
    assert run.status == "partial"
    assert run.intro_summary == "No qualifying robotics or AI stories were selected for this run."
    assert run.candidates[0].rejected_reason == "insufficient_text"
