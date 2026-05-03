import { format, formatDistanceToNowStrict, isValid, parseISO } from "date-fns";

export function toDate(value: string | null | undefined): Date | null {
  if (!value) return null;
  const date = parseISO(value);
  return isValid(date) ? date : null;
}

export function formatBriefDate(value: string | null | undefined): string {
  const date = toDate(value);
  return date ? format(date, "EEEE, MMMM d") : "Unscheduled brief";
}

export function formatTimestamp(value: string | null | undefined): string {
  const date = toDate(value);
  return date ? format(date, "MMM d, h:mm a") : "Time unavailable";
}

export function formatRelative(value: string | null | undefined): string {
  const date = toDate(value);
  return date ? `${formatDistanceToNowStrict(date, { addSuffix: true })}` : "Not completed";
}

export function formatDuration(startedAt: string, completedAt: string | null): string {
  const start = toDate(startedAt);
  const end = toDate(completedAt);
  if (!start || !end) return "In progress";
  const seconds = Math.max(0, Math.round((end.getTime() - start.getTime()) / 1000));
  const minutes = Math.floor(seconds / 60);
  const remainder = seconds % 60;
  return minutes > 0 ? `${minutes}m ${remainder}s` : `${remainder}s`;
}

export function clampNumber(value: number | null | undefined): string {
  return typeof value === "number" ? value.toFixed(1) : "n/a";
}
