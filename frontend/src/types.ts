export type RunStatus = "running" | "completed" | "partial" | "failed";

export type ArticleCategory =
  | "Robotics"
  | "AI Research"
  | "AI Product"
  | "Funding"
  | "Policy";

export interface DataEnvelope<T> {
  data: T;
}

export interface ListEnvelope<T> {
  data: T[];
  meta: {
    total: number;
  };
}

export interface ApiErrorBody {
  detail?: string;
}

export interface RunSummary {
  id: number;
  scheduled_for: string;
  completed_at: string | null;
  status: RunStatus;
  intro_summary: string | null;
  story_count: number;
  social_post_count: number;
}

export interface RunDetail {
  id: number;
  scheduled_for: string;
  started_at: string;
  completed_at: string | null;
  status: RunStatus;
  query_set_version: string;
  intro_summary: string | null;
  selected_articles: SelectedArticle[];
  social_posts: SocialPost[];
  candidates: CandidateArticle[];
}

export interface SelectedArticle {
  id: number;
  canonical_url: string;
  title: string;
  source_name: string;
  author: string | null;
  published_at: string | null;
  category: ArticleCategory;
  summary_short: string;
  why_it_matters: string;
  article_rank: number;
}

export interface SocialPost {
  id: number;
  body: string;
  ordinal: number;
}

export interface CandidateArticle {
  id: number;
  discovered_title: string;
  discovered_url: string;
  source_domain: string;
  discovered_at: string;
  ranking_score: number | null;
  rejected_reason: string | null;
}
