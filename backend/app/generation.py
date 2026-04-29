from app.domain import ArticleSummary, GeneratedPost, RankedArticle


def summarize_articles(selected_articles: list[RankedArticle]) -> list[ArticleSummary]:
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


def generate_intro_summary(summaries: list[ArticleSummary]) -> str:
    if not summaries:
        return "No qualifying robotics or AI stories were selected for this run."
    categories = sorted({item.article.category for item in summaries})
    top_titles = ", ".join(item.article.article.title for item in summaries[:3])
    return _trim(
        f"Today's brief clusters around {', '.join(categories)} with the strongest signals coming from {top_titles}.",
        280,
    )


def generate_social_posts(summaries: list[ArticleSummary]) -> list[GeneratedPost]:
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
