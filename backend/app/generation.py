import json
import logging
from typing import TypeVar

from pydantic import BaseModel

from app.config import get_settings
from app.domain import ArticleSummary, GeneratedPost, RankedArticle


logger = logging.getLogger(__name__)
_DEFAULT_OPENAI_MODEL = "gpt-5.4-mini"
_StructuredResponse = TypeVar("_StructuredResponse", bound=BaseModel)


class _GeneratedArticleSummary(BaseModel):
    summary_short: str
    why_it_matters: str


class _ArticleSummariesResponse(BaseModel):
    summaries: list[_GeneratedArticleSummary]


class _IntroSummaryResponse(BaseModel):
    intro_summary: str


class _SocialPostsResponse(BaseModel):
    posts: list[str]


def summarize_articles(selected_articles: list[RankedArticle]) -> list[ArticleSummary]:
    if not selected_articles:
        return []

    settings = get_settings()
    if _openai_enabled(settings.openai_api_key):
        try:
            return _summarize_articles_with_openai(selected_articles)
        except Exception:
            logger.exception("OpenAI article summarization failed; using deterministic fallback")

    return _summarize_articles_fallback(selected_articles)


def generate_intro_summary(summaries: list[ArticleSummary]) -> str:
    if not summaries:
        return "No qualifying robotics or AI stories were selected for this run."

    settings = get_settings()
    if _openai_enabled(settings.openai_api_key):
        try:
            return _generate_intro_summary_with_openai(summaries)
        except Exception:
            logger.exception("OpenAI intro generation failed; using deterministic fallback")

    return _generate_intro_summary_fallback(summaries)


def generate_social_posts(summaries: list[ArticleSummary]) -> list[GeneratedPost]:
    if not summaries:
        return []

    settings = get_settings()
    if _openai_enabled(settings.openai_api_key):
        try:
            return _generate_social_posts_with_openai(summaries)
        except Exception:
            logger.exception("OpenAI social generation failed; using deterministic fallback")

    return _generate_social_posts_fallback(summaries)


def _summarize_articles_with_openai(selected_articles: list[RankedArticle]) -> list[ArticleSummary]:
    settings = get_settings()
    parsed = _parse_structured_response(
        model=_model_or_default(settings.openai_summarization_model),
        response_format=_ArticleSummariesResponse,
        system_prompt=(
            "You are an editorial analyst for a robotics and AI morning brief. "
            "Return concise, factual summaries from the supplied article text. "
            "Do not add facts that are not supported by the article text."
        ),
        payload={
            "task": "Create one summary object for each article, in the same order.",
            "style": {
                "summary_short": "One sentence, 180-220 characters, dashboard-ready.",
                "why_it_matters": "One sentence, 120-160 characters, focused on business, product, policy, or deployment implications.",
            },
            "articles": [_ranked_article_payload(index, ranked) for index, ranked in enumerate(selected_articles, start=1)],
        },
    )
    if len(parsed.summaries) != len(selected_articles):
        raise ValueError("OpenAI summary count did not match selected article count")

    summaries: list[ArticleSummary] = []
    for ranked, generated in zip(selected_articles, parsed.summaries, strict=True):
        summaries.append(
            ArticleSummary(
                article=ranked,
                summary_short=_trim(generated.summary_short, 240),
                why_it_matters=_trim(generated.why_it_matters, 180),
            )
        )
    return summaries


def _generate_intro_summary_with_openai(summaries: list[ArticleSummary]) -> str:
    settings = get_settings()
    parsed = _parse_structured_response(
        model=_model_or_default(settings.openai_summarization_model),
        response_format=_IntroSummaryResponse,
        system_prompt=(
            "You write compact intro copy for a robotics and AI executive briefing. "
            "Stay factual, specific, and useful for a dashboard hero panel."
        ),
        payload={
            "task": "Write a single intro summary for this run.",
            "constraints": "One sentence, no more than 280 characters.",
            "stories": [_summary_payload(summary) for summary in summaries],
        },
    )
    return _trim(parsed.intro_summary, 280)


def _generate_social_posts_with_openai(summaries: list[ArticleSummary]) -> list[GeneratedPost]:
    settings = get_settings()
    parsed = _parse_structured_response(
        model=_model_or_default(settings.openai_social_model),
        response_format=_SocialPostsResponse,
        system_prompt=(
            "You write copy-paste-ready X posts for a robotics and AI news brief. "
            "Use plain language, avoid hype, and do not invent facts."
        ),
        payload={
            "task": "Write 3 to 5 standalone social posts based only on these summaries.",
            "constraints": "Each post must be under 260 characters. Do not include hashtags unless they are natural.",
            "stories": [_summary_payload(summary) for summary in summaries],
        },
    )
    posts = [_trim(post, 260) for post in parsed.posts if post.strip()]
    if not 3 <= len(posts) <= 5:
        raise ValueError("OpenAI social post count was outside the expected 3-5 range")
    return [GeneratedPost(body=body, ordinal=index) for index, body in enumerate(posts, start=1)]


def _summarize_articles_fallback(selected_articles: list[RankedArticle]) -> list[ArticleSummary]:
    summaries: list[ArticleSummary] = []
    for ranked in selected_articles:
        title = ranked.article.title.strip()
        lead = _first_sentence(ranked.article.cleaned_text)
        summary_short = f"{title}: {lead}"
        why_it_matters = _why_it_matters(ranked)
        summaries.append(
            ArticleSummary(
                article=ranked,
                summary_short=_trim(summary_short, 220),
                why_it_matters=_trim(why_it_matters, 160),
            )
        )
    return summaries


def _generate_intro_summary_fallback(summaries: list[ArticleSummary]) -> str:
    categories = sorted({item.article.category for item in summaries})
    top_titles = ", ".join(item.article.article.title for item in summaries[:3])
    return _trim(
        f"Today's brief clusters around {', '.join(categories)} with the strongest signals coming from {top_titles}.",
        280,
    )


def _generate_social_posts_fallback(summaries: list[ArticleSummary]) -> list[GeneratedPost]:
    posts: list[GeneratedPost] = []
    for ordinal, item in enumerate(summaries[:5], start=1):
        body = _trim(
            f"{item.article.category}: {item.article.article.title}. {item.why_it_matters}",
            260,
        )
        posts.append(GeneratedPost(body=body, ordinal=ordinal))

    if len(posts) < 3 and summaries:
        combined = " ".join(item.why_it_matters for item in summaries[:3])
        while len(posts) < 3:
            posts.append(
                GeneratedPost(
                    body=_trim(f"Morning AI + robotics watch: {combined}", 260),
                    ordinal=len(posts) + 1,
                )
            )
    return posts[:5]


def _parse_structured_response(
    model: str,
    response_format: type[_StructuredResponse],
    system_prompt: str,
    payload: dict[str, object],
) -> _StructuredResponse:
    settings = get_settings()
    api_key = _normalized_openai_api_key(settings.openai_api_key)
    if api_key is None:
        raise ValueError("OPENAI_API_KEY is not configured")

    client = _create_openai_client(api_key)
    response = client.responses.parse(
        model=model,
        input=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=True)},
        ],
        text_format=response_format,
    )
    parsed = getattr(response, "output_parsed", None)
    if parsed is None:
        raise ValueError("OpenAI response did not include parsed structured output")
    return parsed


def _create_openai_client(api_key: str):
    from openai import OpenAI

    return OpenAI(api_key=api_key)


def _ranked_article_payload(index: int, ranked: RankedArticle) -> dict[str, object]:
    article = ranked.article
    return {
        "index": index,
        "title": article.title,
        "source_name": article.source_name,
        "source_domain": article.source_domain,
        "category": ranked.category,
        "ranking_score": ranked.ranking_score,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "canonical_url": article.canonical_url,
        "cleaned_text": _trim(article.cleaned_text, 6000),
    }


def _summary_payload(summary: ArticleSummary) -> dict[str, object]:
    return {
        "title": summary.article.article.title,
        "source_name": summary.article.article.source_name,
        "category": summary.article.category,
        "summary_short": summary.summary_short,
        "why_it_matters": summary.why_it_matters,
    }


def _openai_enabled(api_key: str | None) -> bool:
    return _normalized_openai_api_key(api_key) is not None


def _normalized_openai_api_key(api_key: str | None) -> str | None:
    if api_key is None:
        return None
    stripped = api_key.strip()
    return stripped or None


def _model_or_default(model: str | None) -> str:
    if model and model.strip():
        return model.strip()
    return _DEFAULT_OPENAI_MODEL


def _first_sentence(text: str) -> str:
    sentence = text.split(".")[0].strip()
    return sentence or text[:160].strip()


def _why_it_matters(ranked: RankedArticle) -> str:
    category = ranked.category
    if category == "Robotics":
        return "Shows where physical automation is finding real operational pull instead of demo-only attention."
    if category == "Funding":
        return "Capital concentration here is a strong signal for where operators still expect near-term returns."
    if category == "Policy":
        return "Policy movement can quickly reset deployment timelines, compliance work, and platform risk."
    if category == "AI Research":
        return "Research progress matters when it looks likely to change product capability or deployment cost."
    return "This helps show which AI products are crossing from experimentation into usable workflow adoption."


def _trim(text: str, limit: int) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."
