import type {
  ApiErrorBody,
  DataEnvelope,
  ListEnvelope,
  RunDetail,
  RunSummary
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function requestJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      Accept: "application/json"
    }
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as ApiErrorBody;
      message = body.detail ?? message;
    } catch {
      // Preserve the status-based fallback when the API returns no JSON body.
    }
    throw new ApiError(response.status, message);
  }

  return response.json() as Promise<T>;
}

export async function fetchLatestRun(): Promise<RunDetail> {
  const envelope = await requestJson<DataEnvelope<RunDetail>>("/api/runs/latest");
  return envelope.data;
}

export async function fetchRun(runId: number): Promise<RunDetail> {
  const envelope = await requestJson<DataEnvelope<RunDetail>>(`/api/runs/${runId}`);
  return envelope.data;
}

export async function fetchRuns(): Promise<RunSummary[]> {
  const envelope = await requestJson<ListEnvelope<RunSummary>>("/api/runs");
  return envelope.data;
}
