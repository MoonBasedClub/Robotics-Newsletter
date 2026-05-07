from datetime import UTC, datetime
from types import SimpleNamespace

from app import generation
from app.domain import ArticleSummary, ExtractedArticle, RankedArticle


class _FakeResponses:
    def __init__(self, parsed_outputs):
        self.parsed_outputs = list(parsed_outputs)
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        parsed = self.parsed_outputs.pop(0)
        if isinstance(parsed, Exception):
            raise parsed
        return SimpleNamespace(output_parsed=parsed)


class _FakeClient:
    def __init__(self, parsed_outputs):
        self.responses = _FakeResponses(parsed_outputs)


def _ranked_article() -> RankedArticle:
    article = ExtractedArticle(
        discovered_title="Humanoid robots enter warehouse pilot",
        discovered_url="https://example.com/humanoid-pilot",
        source_domain="example.com",
        discovered_at=datetime(2026, 5, 4, 13, 0, tzinfo=UTC),
        canonical_url="https://example.com/humanoid-pilot",
        title="Humanoid robots enter warehouse pilot",
        source_name="Example Robotics",
        author=None,
        published_at=datetime(2026, 5, 4, 12, 30, tzinfo=UTC),
        cleaned_text="Humanoid robots are moving into warehouse pilots with measurable throughput goals. " * 8,
    )
    return RankedArticle(article=article, ranking_score=9.1, category="Robotics")


def _settings(api_key: str | None = "test-key"):
    return SimpleNamespace(
        openai_api_key=api_key,
        openai_summarization_model="gpt-5.4-mini",
        openai_social_model="gpt-5.4-mini",
    )


def test_summarize_articles_uses_openai_structured_outputs(monkeypatch):
    client = _FakeClient(
        [
            generation._ArticleSummariesResponse(
                summaries=[
                    generation._GeneratedArticleSummary(
                        summary_short="Humanoid robots are entering warehouse pilots with measurable operating goals.",
                        why_it_matters="This points to robotics buyers evaluating deployment value against concrete labor constraints.",
                    )
                ]
            )
        ]
    )
    monkeypatch.setattr(generation, "get_settings", lambda: _settings())
    monkeypatch.setattr(generation, "_create_openai_client", lambda api_key: client)

    summaries = generation.summarize_articles([_ranked_article()])

    assert summaries[0].summary_short.startswith("Humanoid robots are entering")
    assert summaries[0].why_it_matters.startswith("This points to robotics buyers")
    assert client.responses.calls[0]["model"] == "gpt-5.4-mini"
    assert client.responses.calls[0]["text_format"] is generation._ArticleSummariesResponse


def test_intro_and_social_posts_use_openai_structured_outputs(monkeypatch):
    client = _FakeClient(
        [
            generation._IntroSummaryResponse(
                intro_summary="Today's brief centers on robotics moving from demos into measurable warehouse operations."
            ),
            generation._SocialPostsResponse(
                posts=[
                    "Humanoid robots are being tested against warehouse throughput goals, not just demo appeal.",
                    "The robotics signal today is practical: buyers want deployment metrics before wider rollout.",
                    "Warehouse automation keeps shifting toward measurable pilots with clear labor-fit questions.",
                ]
            ),
        ]
    )
    ranked = _ranked_article()
    summary = ArticleSummary(
        article=ranked,
        summary_short="Humanoid robots are entering warehouse pilots with measurable operating goals.",
        why_it_matters="This points to robotics buyers evaluating deployment value against concrete labor constraints.",
    )
    monkeypatch.setattr(generation, "get_settings", lambda: _settings())
    monkeypatch.setattr(generation, "_create_openai_client", lambda api_key: client)

    intro = generation.generate_intro_summary([summary])
    posts = generation.generate_social_posts([summary])

    assert intro.startswith("Today's brief centers")
    assert len(posts) == 3
    assert posts[0].ordinal == 1
    assert client.responses.calls[0]["text_format"] is generation._IntroSummaryResponse
    assert client.responses.calls[1]["text_format"] is generation._SocialPostsResponse


def test_generation_falls_back_without_openai_api_key(monkeypatch):
    monkeypatch.setattr(generation, "get_settings", lambda: _settings(api_key=""))

    summaries = generation.summarize_articles([_ranked_article()])
    intro = generation.generate_intro_summary(summaries)
    posts = generation.generate_social_posts(summaries)

    assert summaries[0].summary_short.startswith("Humanoid robots enter warehouse pilot:")
    assert intro.startswith("Today's brief clusters around Robotics")
    assert len(posts) >= 1


def test_generation_falls_back_when_openai_raises(monkeypatch):
    client = _FakeClient([RuntimeError("api unavailable")])
    monkeypatch.setattr(generation, "get_settings", lambda: _settings())
    monkeypatch.setattr(generation, "_create_openai_client", lambda api_key: client)

    summaries = generation.summarize_articles([_ranked_article()])

    assert summaries[0].summary_short.startswith("Humanoid robots enter warehouse pilot:")
