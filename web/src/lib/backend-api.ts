import type { EmilyResponse } from "@/lib/emily-api";
import type { DraftRecord, JournalRecord } from "@/lib/user-data";

export interface AuthUser {
  user_id: string;
  username: string;
}

interface AuthResponse {
  token: string;
  user_id: string;
  username: string;
}

const TOKEN_KEY = "echo-auth-token";

function getToken(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(TOKEN_KEY) ?? "";
}

function setToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
}

export function hasToken(): boolean {
  return Boolean(getToken());
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers || {}),
    },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function register(username: string, password: string): Promise<AuthUser> {
  const data = await request<AuthResponse>("/api/backend/auth/register", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  setToken(data.token);
  return { user_id: data.user_id, username: data.username };
}

export async function login(username: string, password: string): Promise<AuthUser> {
  const data = await request<AuthResponse>("/api/backend/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
  setToken(data.token);
  return { user_id: data.user_id, username: data.username };
}

export async function me(): Promise<AuthUser> {
  return request<AuthUser>("/api/backend/auth/me");
}

export async function logout(): Promise<void> {
  try {
    await request<{ ok: boolean }>("/api/backend/auth/logout", { method: "POST" });
  } finally {
    clearToken();
  }
}

export async function analyzeJournal(payload: {
  request_id: string;
  user_id: string;
  user_input: string;
  trace_id: string;
  metadata?: Record<string, unknown>;
}): Promise<EmilyResponse> {
  return request<EmilyResponse>("/api/pipeline/analyze", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function getEntries(): Promise<JournalRecord[]> {
  return request<JournalRecord[]>("/api/backend/data/entries");
}

export async function getDrafts(): Promise<DraftRecord[]> {
  return request<DraftRecord[]>("/api/backend/data/drafts");
}

export async function saveDraft(text: string, mood: string | null): Promise<DraftRecord> {
  return request<DraftRecord>("/api/backend/data/drafts", {
    method: "POST",
    body: JSON.stringify({ text, mood }),
  });
}

export async function deleteDraft(draftId: string): Promise<void> {
  await request<{ ok: boolean }>(`/api/backend/data/drafts/${draftId}`, { method: "DELETE" });
}

export async function getServerInsights(): Promise<string[]> {
  const data = await request<{ insights: string[] }>("/api/backend/data/insights");
  return data.insights;
}

export async function requestPasswordReset(username: string): Promise<string | null> {
  const data = await request<{ ok: boolean; reset_token?: string | null }>("/api/backend/auth/password-reset/request", {
    method: "POST",
    body: JSON.stringify({ username }),
  });
  return data.reset_token ?? null;
}

export async function confirmPasswordReset(token: string, newPassword: string): Promise<void> {
  await request<{ ok: boolean }>("/api/backend/auth/password-reset/confirm", {
    method: "POST",
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

export async function updateEntry(entryId: string, text: string, mood: string | null): Promise<JournalRecord> {
  return request<JournalRecord>(`/api/backend/data/entries/${entryId}`, {
    method: "PUT",
    body: JSON.stringify({ text, mood }),
  });
}

export async function deleteEntry(entryId: string): Promise<void> {
  await request<{ ok: boolean }>(`/api/backend/data/entries/${entryId}`, { method: "DELETE" });
}
