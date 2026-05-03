import { useEffect, useMemo, useState } from "react";
import { Link, NavLink, Route, Routes, useNavigate, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowLeft,
  Check,
  Copy,
  ExternalLink,
  Moon,
  RefreshCw,
  Sun,
  TerminalSquare
} from "lucide-react";
import { ApiError, fetchLatestRun, fetchRun, fetchRuns } from "./api";
import {
  clampNumber,
  formatBriefDate,
  formatDuration,
  formatRelative,
  formatTimestamp
} from "./format";
import type {
  ArticleCategory,
  CandidateArticle,
  RunDetail,
  RunStatus,
  RunSummary,
  SelectedArticle,
  SocialPost
} from "./types";

type Theme = "light" | "dark";

const statusLabel: Record<RunStatus, string> = {
  running: "Running",
  completed: "Completed",
  partial: "Partial",
  failed: "Failed"
};

const rejectionLabel: Record<string, string> = {
  duplicate: "Duplicate",
  duplicate_title: "Similar story",
  below_cutoff: "Not selected",
  insufficient_text: "Too little text",
  extraction_failed: "Extraction failed"
};

const categoryClassName: Record<ArticleCategory, string> = {
  Robotics: "category-robotics",
  "AI Research": "category-ai-research",
  "AI Product": "category-ai-product",
  Funding: "category-funding",
  Policy: "category-policy"
};

function useTheme(): [Theme, () => void] {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem("news-scraper-theme");
    if (saved === "dark" || saved === "light") return saved;
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("news-scraper-theme", theme);
  }, [theme]);

  return [theme, () => setTheme((current) => (current === "dark" ? "light" : "dark"))];
}

function App() {
  const [theme, toggleTheme] = useTheme();

  return (
    <Routes>
      <Route
        path="/"
        element={<DashboardPage mode="latest" theme={theme} toggleTheme={toggleTheme} />}
      />
      <Route
        path="/runs/:runId"
        element={<DashboardPage mode="archive" theme={theme} toggleTheme={toggleTheme} />}
      />
    </Routes>
  );
}

interface DashboardPageProps {
  mode: "latest" | "archive";
  theme: Theme;
  toggleTheme: () => void;
}

function DashboardPage({ mode, theme, toggleTheme }: DashboardPageProps) {
  const params = useParams();
  const navigate = useNavigate();
  const runId = Number(params.runId);
  const isArchive = mode === "archive";

  const runsQuery = useQuery({
    queryKey: ["runs"],
    queryFn: fetchRuns
  });

  const runQuery = useQuery({
    queryKey: isArchive ? ["run", runId] : ["run", "latest"],
    queryFn: () => (isArchive ? fetchRun(runId) : fetchLatestRun()),
    enabled: !isArchive || Number.isInteger(runId),
    refetchInterval: (query) => (query.state.data?.status === "running" ? 30_000 : false)
  });

  const hasNoRuns =
    runQuery.error instanceof ApiError &&
    runQuery.error.status === 404 &&
    !isArchive &&
    runQuery.error.message === "No runs available";

  const selectedRun = runQuery.data;
  const runs = runsQuery.data ?? [];

  useEffect(() => {
    if (isArchive && (!Number.isInteger(runId) || runId <= 0)) {
      navigate("/", { replace: true });
    }
  }, [isArchive, navigate, runId]);

  return (
    <div className="app-shell">
      <AppHeader
        run={selectedRun}
        isArchive={isArchive}
        isRefreshing={runQuery.isFetching}
        theme={theme}
        onRefresh={() => {
          void runQuery.refetch();
          void runsQuery.refetch();
        }}
        onToggleTheme={toggleTheme}
      />

      <div className="layout">
        <NavigationRail runs={runs} selectedRunId={selectedRun?.id} isArchive={isArchive} />

        <main className="content" id="main-content">
          {isArchive && (
            <Link className="back-link" to="/">
              <ArrowLeft size={16} aria-hidden="true" />
              Latest brief
            </Link>
          )}

          {runQuery.isLoading ? (
            <DashboardSkeleton />
          ) : hasNoRuns ? (
            <EmptyBackend />
          ) : runQuery.isError ? (
            <LoadError error={runQuery.error} onRetry={() => void runQuery.refetch()} />
          ) : selectedRun ? (
            <DashboardContent
              run={selectedRun}
              archiveRuns={runs}
              archiveLoading={runsQuery.isLoading}
              isArchive={isArchive}
            />
          ) : null}
        </main>
      </div>
    </div>
  );
}

interface AppHeaderProps {
  run?: RunDetail;
  isArchive: boolean;
  isRefreshing: boolean;
  theme: Theme;
  onRefresh: () => void;
  onToggleTheme: () => void;
}

function AppHeader({
  run,
  isArchive,
  isRefreshing,
  theme,
  onRefresh,
  onToggleTheme
}: AppHeaderProps) {
  return (
    <header className="app-header">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <div className="header-inner">
        <div>
          <p className="eyebrow">Robotics + AI</p>
          <Link className="brand" to="/">
            Morning Brief
          </Link>
        </div>
        <div className="header-meta" aria-label="Current run status">
          <span>{isArchive ? "Archive view" : "Latest run"}</span>
          <span aria-hidden="true">/</span>
          <span>{run ? formatBriefDate(run.scheduled_for) : "Waiting for run"}</span>
          {run && <StatusPill status={run.status} compact />}
        </div>
        <div className="header-actions">
          <button className="icon-button" type="button" onClick={onRefresh} aria-label="Refresh data">
            <RefreshCw size={18} className={isRefreshing ? "spin" : undefined} aria-hidden="true" />
          </button>
          <button
            className="icon-button"
            type="button"
            onClick={onToggleTheme}
            aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} theme`}
          >
            {theme === "dark" ? <Sun size={18} aria-hidden="true" /> : <Moon size={18} aria-hidden="true" />}
          </button>
        </div>
      </div>
    </header>
  );
}

interface NavigationRailProps {
  runs: RunSummary[];
  selectedRunId?: number;
  isArchive: boolean;
}

function NavigationRail({ runs, selectedRunId, isArchive }: NavigationRailProps) {
  return (
    <aside className="rail" aria-label="Dashboard navigation">
      <nav className="section-nav">
        <a href="#brief">Morning Brief</a>
        <a href="#stories">Top Stories</a>
        <a href="#social">Social Posts</a>
        <a href="#archive">Archive</a>
      </nav>
      <div className="rail-archive">
        <p className="rail-title">Run History</p>
        <NavLink className={({ isActive }) => `rail-run ${isActive && !isArchive ? "active" : ""}`} to="/">
          <span>Latest</span>
          <span>Now</span>
        </NavLink>
        {runs.slice(0, 5).map((run) => (
          <NavLink
            className={({ isActive }) => `rail-run ${isActive || selectedRunId === run.id ? "active" : ""}`}
            key={run.id}
            to={`/runs/${run.id}`}
          >
            <span>{formatBriefDate(run.scheduled_for)}</span>
            <StatusDot status={run.status} />
          </NavLink>
        ))}
      </div>
    </aside>
  );
}

interface DashboardContentProps {
  run: RunDetail;
  archiveRuns: RunSummary[];
  archiveLoading: boolean;
  isArchive: boolean;
}

function DashboardContent({ run, archiveRuns, archiveLoading, isArchive }: DashboardContentProps) {
  const sortedStories = useMemo(
    () => [...run.selected_articles].sort((a, b) => a.article_rank - b.article_rank),
    [run.selected_articles]
  );
  const sortedPosts = useMemo(
    () => [...run.social_posts].sort((a, b) => a.ordinal - b.ordinal),
    [run.social_posts]
  );
  const featured = sortedStories[0];
  const remaining = sortedStories.slice(1);

  return (
    <>
      <MorningBriefPanel run={run} isArchive={isArchive} />

      <section className="section" id="stories" aria-labelledby="stories-title">
        <SectionHeader
          id="stories-title"
          title="Top Stories"
          description="Ranked articles selected for the morning robotics and AI scan."
        />
        {sortedStories.length === 0 ? (
          <EmptySection title="No selected stories" body="The run completed without qualifying articles." />
        ) : (
          <>
            {featured && <StoryCard article={featured} featured />}
            <div className="story-grid">
              {remaining.map((article) => (
                <StoryCard key={article.id} article={article} />
              ))}
            </div>
          </>
        )}
      </section>

      <SocialPostsPanel posts={sortedPosts} />
      <DiagnosticsPanel candidates={run.candidates} />
      <ArchiveList runs={archiveRuns} loading={archiveLoading} selectedRunId={run.id} />
    </>
  );
}

function MorningBriefPanel({ run, isArchive }: { run: RunDetail; isArchive: boolean }) {
  const rejectedCount = run.candidates.filter((candidate) => candidate.rejected_reason).length;
  return (
    <section className="brief-panel" id="brief" aria-labelledby="brief-title">
      <div className="brief-content">
        <div className="brief-kicker">
          <StatusPill status={run.status} />
          <span>{isArchive ? "Archived run" : "Latest briefing"}</span>
        </div>
        <h1 id="brief-title">{formatBriefDate(run.scheduled_for)}</h1>
        <p className="brief-summary">
          {run.intro_summary ??
            "The worker has not saved an intro summary for this run. Stories and diagnostics are still available below."}
        </p>
      </div>
      <div className="brief-stats" aria-label="Run metrics">
        <KpiStat label="Selected stories" value={run.selected_articles.length.toString()} helper="ranked for scan" />
        <KpiStat label="Candidates" value={run.candidates.length.toString()} helper={`${rejectedCount} rejected`} />
        <KpiStat label="Social posts" value={run.social_posts.length.toString()} helper="copy-ready outputs" />
        <KpiStat label="Runtime" value={formatDuration(run.started_at, run.completed_at)} helper={formatRelative(run.completed_at)} />
      </div>
      {(run.status === "partial" || run.status === "failed") && (
        <div className={`run-alert ${run.status}`} role="status">
          <strong>{statusLabel[run.status]} run.</strong>
          <span>
            {run.status === "partial"
              ? "The shell and diagnostics are available, but selected output may be incomplete."
              : "The worker failed before completing the full brief. Any saved content remains visible."}
          </span>
        </div>
      )}
    </section>
  );
}

function KpiStat({ label, value, helper }: { label: string; value: string; helper: string }) {
  return (
    <div className="kpi-stat">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{helper}</small>
    </div>
  );
}

interface StoryCardProps {
  article: SelectedArticle;
  featured?: boolean;
}

function StoryCard({ article, featured = false }: StoryCardProps) {
  return (
    <article className={`story-card ${featured ? "featured" : ""}`}>
      <div className="story-rank">#{article.article_rank}</div>
      <div className="story-body">
        <div className="story-meta">
          <span>{article.source_name}</span>
          <span>{formatTimestamp(article.published_at)}</span>
          <Badge className={categoryClassName[article.category]}>{article.category}</Badge>
        </div>
        <h2>{article.title}</h2>
        <p>{article.summary_short}</p>
        <div className="why-block">
          <span>Why it matters</span>
          <p>{article.why_it_matters}</p>
        </div>
        <a className="source-link" href={article.canonical_url} target="_blank" rel="noreferrer">
          Read source
          <ExternalLink size={16} aria-hidden="true" />
        </a>
      </div>
    </article>
  );
}

function SocialPostsPanel({ posts }: { posts: SocialPost[] }) {
  return (
    <section className="section" id="social" aria-labelledby="social-title">
      <SectionHeader
        id="social-title"
        title="Social Posts"
        description="Generated copy blocks, preserved exactly for one-click copying."
      />
      {posts.length === 0 ? (
        <EmptySection title="No social posts" body="This run did not produce shareable copy." />
      ) : (
        <div className="social-grid">
          {posts.map((post) => (
            <CopyBlock key={post.id} post={post} />
          ))}
        </div>
      )}
    </section>
  );
}

function CopyBlock({ post }: { post: SocialPost }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(post.body);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }

  return (
    <article className="copy-block">
      <div className="copy-head">
        <span>Post {post.ordinal}</span>
        <span>{post.body.length} chars</span>
      </div>
      <p>{post.body}</p>
      <button className="copy-button" type="button" onClick={handleCopy}>
        {copied ? <Check size={16} aria-hidden="true" /> : <Copy size={16} aria-hidden="true" />}
        {copied ? "Copied" : "Copy"}
      </button>
      <span className="sr-only" aria-live="polite">
        {copied ? `Post ${post.ordinal} copied` : ""}
      </span>
    </article>
  );
}

function DiagnosticsPanel({ candidates }: { candidates: CandidateArticle[] }) {
  const rejectedCount = candidates.filter((candidate) => candidate.rejected_reason).length;
  return (
    <section className="section diagnostics" aria-labelledby="diagnostics-title">
      <details>
        <summary>
          <span>
            <TerminalSquare size={18} aria-hidden="true" />
            Pipeline Diagnostics
          </span>
          <small>
            {candidates.length} candidates / {rejectedCount} rejected
          </small>
        </summary>
        {candidates.length === 0 ? (
          <EmptySection title="No candidates saved" body="The backend did not persist discovery diagnostics for this run." />
        ) : (
          <div className="candidate-table" role="table" aria-label="Candidate diagnostics">
            <div className="candidate-row candidate-head" role="row">
              <span role="columnheader">Source</span>
              <span role="columnheader">Title</span>
              <span role="columnheader">Score</span>
              <span role="columnheader">Result</span>
            </div>
            {candidates.slice(0, 12).map((candidate) => (
              <a
                className="candidate-row"
                href={candidate.discovered_url}
                key={candidate.id}
                rel="noreferrer"
                role="row"
                target="_blank"
              >
                <span role="cell">{candidate.source_domain}</span>
                <span role="cell">{candidate.discovered_title}</span>
                <span role="cell">{clampNumber(candidate.ranking_score)}</span>
                <span role="cell">
                  {candidate.rejected_reason ? rejectionLabel[candidate.rejected_reason] ?? candidate.rejected_reason : "Selected"}
                </span>
              </a>
            ))}
          </div>
        )}
      </details>
    </section>
  );
}

interface ArchiveListProps {
  runs: RunSummary[];
  loading: boolean;
  selectedRunId?: number;
}

function ArchiveList({ runs, loading, selectedRunId }: ArchiveListProps) {
  return (
    <section className="section" id="archive" aria-labelledby="archive-title">
      <SectionHeader id="archive-title" title="Archive" description="Reverse-chronological run history." />
      {loading ? (
        <div className="archive-loading">Loading archive...</div>
      ) : runs.length === 0 ? (
        <EmptySection title="No archived runs" body="Runs will appear here after the worker saves output." />
      ) : (
        <div className="archive-list">
          {runs.map((run) => (
            <Link
              className={`archive-row ${selectedRunId === run.id ? "active" : ""}`}
              key={run.id}
              to={`/runs/${run.id}`}
            >
              <div>
                <strong>{formatBriefDate(run.scheduled_for)}</strong>
                <span>{run.intro_summary ?? "No intro summary saved."}</span>
              </div>
              <div className="archive-metrics">
                <StatusPill status={run.status} compact />
                <span>{run.story_count} stories</span>
                <span>{run.social_post_count} posts</span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}

function SectionHeader({ id, title, description }: { id: string; title: string; description: string }) {
  return (
    <div className="section-header">
      <div>
        <p className="eyebrow">Dashboard</p>
        <h2 id={id}>{title}</h2>
      </div>
      <p>{description}</p>
    </div>
  );
}

function StatusPill({ status, compact = false }: { status: RunStatus; compact?: boolean }) {
  return (
    <span className={`status-pill ${status} ${compact ? "compact" : ""}`}>
      <StatusDot status={status} />
      {statusLabel[status]}
    </span>
  );
}

function StatusDot({ status }: { status: RunStatus }) {
  return <span className={`status-dot ${status}`} aria-hidden="true" />;
}

function Badge({ children, className }: { children: string; className: string }) {
  return <span className={`badge ${className}`}>{children}</span>;
}

function EmptyBackend() {
  return (
    <section className="empty-state">
      <h1>No runs available</h1>
      <p>The API is healthy enough to respond, but the worker has not saved a morning brief yet.</p>
      <Link className="button-link" to="/">
        Check latest
      </Link>
    </section>
  );
}

function EmptySection({ title, body }: { title: string; body: string }) {
  return (
    <div className="empty-section">
      <strong>{title}</strong>
      <p>{body}</p>
    </div>
  );
}

function LoadError({ error, onRetry }: { error: unknown; onRetry: () => void }) {
  const message = error instanceof Error ? error.message : "The dashboard could not load this run.";
  return (
    <section className="empty-state error">
      <h1>Unable to load brief</h1>
      <p>{message}</p>
      <button className="button-link" type="button" onClick={onRetry}>
        Retry
      </button>
    </section>
  );
}

function DashboardSkeleton() {
  return (
    <>
      <section className="brief-panel skeleton-panel" aria-label="Loading morning brief">
        <div className="skeleton-line wide" />
        <div className="skeleton-line title" />
        <div className="skeleton-line" />
        <div className="skeleton-line short" />
      </section>
      <div className="story-grid">
        <div className="skeleton-card" />
        <div className="skeleton-card" />
      </div>
    </>
  );
}

export default App;
