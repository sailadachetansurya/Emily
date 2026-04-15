import type { EmotionState } from "@/lib/emily-api";

export interface JournalRecord {
  id: string;
  text: string;
  mood: string | null;
  responseText: string;
  emotionState: EmotionState | null;
  createdAt: string;
  triggers: string[];
}

export interface DraftRecord {
  id: string;
  text: string;
  mood: string | null;
  createdAt: string;
}

export interface UserSnapshot {
  draft: string;
  mood: string | null;
  entries: JournalRecord[];
  drafts: DraftRecord[];
}

export const ACTIVE_USER_KEY = "echo-active-user";
const MAX_ENTRIES = 80;
const MAX_DRAFTS = 40;

export const EMPTY_SNAPSHOT: UserSnapshot = {
  draft: "",
  mood: null,
  entries: [],
  drafts: [],
};

const TRIGGER_RULES: Array<{ name: string; keywords: string[] }> = [
  { name: "Work Stress", keywords: ["work", "job", "office", "deadline", "boss"] },
  { name: "Social Media", keywords: ["instagram", "social", "online", "scroll", "twitter"] },
  { name: "Late Nights", keywords: ["late", "night", "sleep", "insomnia", "tired"] },
  { name: "Unresolved Talks", keywords: ["fight", "argument", "talk", "family", "friend"] },
  { name: "Financial Worry", keywords: ["money", "rent", "debt", "finance", "bills"] },
];

function hasWindow(): boolean {
  return typeof window !== "undefined";
}

export function getUserStorageKey(userId: string): string {
  return `echo-user-${userId}`;
}

export function getActiveUser(): string {
  if (!hasWindow()) return "";
  return localStorage.getItem(ACTIVE_USER_KEY) ?? "";
}

export function setActiveUser(userId: string): void {
  if (!hasWindow()) return;
  localStorage.setItem(ACTIVE_USER_KEY, userId);
}

export function clearActiveUser(): void {
  if (!hasWindow()) return;
  localStorage.removeItem(ACTIVE_USER_KEY);
}

export function getSnapshot(userId: string): UserSnapshot {
  if (!hasWindow() || !userId) return { ...EMPTY_SNAPSHOT };
  const raw = localStorage.getItem(getUserStorageKey(userId));
  if (!raw) return { ...EMPTY_SNAPSHOT };
  try {
    const parsed = JSON.parse(raw) as UserSnapshot;
    return {
      draft: parsed.draft ?? "",
      mood: parsed.mood ?? null,
      entries: parsed.entries ?? [],
      drafts: parsed.drafts ?? [],
    };
  } catch {
    return { ...EMPTY_SNAPSHOT };
  }
}

export function saveSnapshot(userId: string, snapshot: UserSnapshot): void {
  if (!hasWindow() || !userId) return;
  localStorage.setItem(getUserStorageKey(userId), JSON.stringify(snapshot));
}

export function appendEntry(snapshot: UserSnapshot, next: JournalRecord): UserSnapshot {
  return {
    ...snapshot,
    entries: [next, ...snapshot.entries].slice(0, MAX_ENTRIES),
  };
}

export function appendDraft(snapshot: UserSnapshot, text: string): UserSnapshot {
  if (!text.trim()) return snapshot;
  const nextDraft: DraftRecord = {
    id: `draft-${Date.now()}`,
    text: text.trim(),
    mood: snapshot.mood,
    createdAt: new Date().toISOString(),
  };
  return {
    ...snapshot,
    drafts: [nextDraft, ...snapshot.drafts].slice(0, MAX_DRAFTS),
  };
}

export function deleteDraft(snapshot: UserSnapshot, draftId: string): UserSnapshot {
  return {
    ...snapshot,
    drafts: snapshot.drafts.filter((d) => d.id !== draftId),
  };
}

export function extractTriggers(text: string): string[] {
  const normalized = text.toLowerCase();
  return TRIGGER_RULES.filter((rule) => rule.keywords.some((k) => normalized.includes(k))).map((rule) => rule.name);
}

export function toMoodLabel(entries: JournalRecord[]): string {
  if (!entries.length) return "No data";
  const scoreByMood: Record<string, number> = { Anxious: -2, Sad: -1, Neutral: 0, Good: 1, Great: 2 };
  const scored = entries.map((entry) => scoreByMood[entry.mood ?? "Neutral"] ?? 0);
  const avg = scored.reduce((sum, v) => sum + v, 0) / scored.length;
  if (avg >= 1.5) return "Great";
  if (avg >= 0.5) return "Good";
  if (avg > -0.5) return "Neutral";
  if (avg > -1.5) return "Sad";
  return "Anxious";
}

export function buildInsights(entries: JournalRecord[]): string[] {
  if (!entries.length) return ["No insights yet. Add journal entries to unlock pattern insights."];
  const averageValence =
    entries.reduce((sum, e) => sum + (e.emotionState?.emotional_valence ?? 0), 0) / entries.length;
  const triggerCounts = new Map<string, number>();
  for (const entry of entries) {
    for (const trigger of entry.triggers) {
      triggerCounts.set(trigger, (triggerCounts.get(trigger) ?? 0) + 1);
    }
  }
  const topTrigger = Array.from(triggerCounts.entries()).sort((a, b) => b[1] - a[1])[0]?.[0];
  const results = [
    averageValence < -0.2
      ? "Trend: recent valence looks low. Try smaller recovery routines."
      : "Trend: recent valence is stable or improving.",
    `Mood trend: ${toMoodLabel(entries)}.`,
  ];
  if (topTrigger) results.push(`Top trigger: ${topTrigger}.`);
  return results;
}

export function formatLocalDate(iso: string): string {
  return new Date(iso).toLocaleString();
}
