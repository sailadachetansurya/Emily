"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { BentoGrid, BentoItem } from "@/components/BentoGrid";
import Card from "@/components/Card";
import Button from "@/components/Button";
import { Input } from "@/components/Input";
import type { EmilyResponse, EmotionState } from "@/lib/emily-api";
import {
  analyzeJournal,
  confirmPasswordReset,
  getDrafts,
  getEntries,
  getServerInsights,
  login,
  logout,
  me,
  register,
  requestPasswordReset,
  saveDraft,
} from "@/lib/backend-api";
import { buildInsights, formatLocalDate, JournalRecord, toMoodLabel } from "@/lib/user-data";

type AccentColor = "violet" | "green" | "orange" | "pink" | "cyan";

export default function Home() {
  const [authUser, setAuthUser] = useState<{ user_id: string; username: string } | null>(null);
  const [usernameInput, setUsernameInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [isResetMode, setIsResetMode] = useState(false);
  const [resetTokenInput, setResetTokenInput] = useState("");

  const [journalEntry, setJournalEntry] = useState("");
  const [mood, setMood] = useState<string | null>(null);
  const [entries, setEntries] = useState<JournalRecord[]>([]);
  const [draftCount, setDraftCount] = useState(0);
  const [serverInsights, setServerInsights] = useState<string[]>([]);
  const [selectedTrigger, setSelectedTrigger] = useState<string | null>(null);

  const [emilyResponse, setEmilyResponse] = useState<EmilyResponse | null>(null);
  const [emotionState, setEmotionState] = useState<EmotionState | null>(null);
  const [statusMessage, setStatusMessage] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isHydrating, setIsHydrating] = useState(true);

  const { scrollY } = useScroll();
  const heroY = useTransform(scrollY, [0, 500], [0, -120]);
  const heroOpacity = useTransform(scrollY, [0, 400], [1, 0.4]);

  const moods = [
    { label: "Anxious", emoji: "😰" },
    { label: "Sad", emoji: "😔" },
    { label: "Neutral", emoji: "😐" },
    { label: "Good", emoji: "🙂" },
    { label: "Great", emoji: "🤩" },
  ] as const;

  const loadServerData = async () => {
    const [nextEntries, nextDrafts, insights] = await Promise.all([getEntries(), getDrafts(), getServerInsights()]);
    setEntries(nextEntries);
    setDraftCount(nextDrafts.length);
    setServerInsights(insights);
  };

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const user = await me();
        setAuthUser(user);
        setUsernameInput(user.username);
        await loadServerData();
      } catch {
        setAuthUser(null);
      } finally {
        setIsHydrating(false);
      }
    };
    void bootstrap();
  }, []);

  const triggerCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const entry of entries) {
      const text = entry.text.toLowerCase();
      for (const k of ["work", "social", "night", "money", "family", "friend"]) {
        if (text.includes(k)) counts.set(k, (counts.get(k) ?? 0) + 1);
      }
    }
    return Array.from(counts.entries()).sort((a, b) => b[1] - a[1]);
  }, [entries]);

  const localInsights = useMemo(() => buildInsights(entries), [entries]);
  const insights = serverInsights.length ? serverInsights : localInsights;

  const getEmotionColor = (): AccentColor => {
    if (!emotionState) return "violet";
    if (emotionState.emotional_valence < -0.3) return "orange";
    if (emotionState.emotional_valence > 0.3) return "green";
    return "violet";
  };

  const responseAccent = getEmotionColor();
  const isFallbackResponse =
    emilyResponse?.traces.some((t) => t.stage_name === "fallback" || t.stage_name === "error") ||
    emilyResponse?.response.safety_notes.some((n) => n.toLowerCase().includes("fallback")) ||
    false;
  const responseDotClass = {
    violet: "text-electric-violet",
    green: "text-electric-green",
    orange: "text-electric-orange",
    pink: "text-electric-pink",
    cyan: "text-electric-cyan",
  }[responseAccent];

  const handleAuth = async () => {
    if (!usernameInput.trim() || !passwordInput.trim()) return;
    setError(null);
    setStatusMessage("");
    try {
      const user = isRegisterMode
        ? await register(usernameInput.trim().toLowerCase(), passwordInput)
        : await login(usernameInput.trim().toLowerCase(), passwordInput);
      setAuthUser(user);
      setPasswordInput("");
      await loadServerData();
      setStatusMessage(isRegisterMode ? "Account created." : "Logged in.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Auth failed");
    }
  };

  const handleResetRequest = async () => {
    if (!usernameInput.trim()) return;
    try {
      const token = await requestPasswordReset(usernameInput.trim().toLowerCase());
      setStatusMessage(token ? `Reset token: ${token}` : "If user exists, token generated.");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reset request failed");
    }
  };

  const handleResetConfirm = async () => {
    if (!resetTokenInput.trim() || !passwordInput.trim()) return;
    try {
      await confirmPasswordReset(resetTokenInput.trim(), passwordInput);
      setStatusMessage("Password reset complete. Login now.");
      setIsResetMode(false);
      setResetTokenInput("");
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Reset confirm failed");
    }
  };

  const handleLogout = async () => {
    await logout();
    setAuthUser(null);
    setEntries([]);
    setDraftCount(0);
    setServerInsights([]);
    setStatusMessage("");
    setError(null);
  };

  const handleAnalyze = async () => {
    if (!authUser || !journalEntry.trim()) return;
    setIsLoading(true);
    setError(null);
    setStatusMessage("");

    try {
      const response = await analyzeJournal({
        request_id: `req-${Date.now()}`,
        user_id: authUser.username,
        user_input: journalEntry,
        trace_id: `trace-${Date.now()}`,
        metadata: { mood },
      });
      setEmilyResponse(response);
      const emotionTrace = response.traces.find((t) => t.stage_name === "emotion_perception");
      setEmotionState((emotionTrace?.metadata?.emotion as EmotionState) ?? null);
      setJournalEntry("");
      await loadServerData();
      setStatusMessage(
        response.traces.some((t) => t.stage_name === "fallback")
          ? "Analyzed with fallback mode."
          : "Analyzed and auto-saved to server.",
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analyze failed");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveDraft = async () => {
    if (!journalEntry.trim()) return;
    try {
      await saveDraft(journalEntry, mood);
      await loadServerData();
      setStatusMessage("Draft saved to server.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save draft failed");
    }
  };

  if (isHydrating) {
    return <main className="min-h-screen p-8 font-mono text-sm">Loading...</main>;
  }

  if (!authUser) {
    return (
      <main className="min-h-screen p-4 md:p-8 flex items-center justify-center">
        <Card className="w-full max-w-xl p-8 border-electric-violet" variant="accent" accentColor="violet">
          <h1 className="text-3xl font-display mb-2">ECHO</h1>
          <p className="font-mono text-textMuted text-xs mb-6">Emotional Chronicle Helping Observations</p>
          <Input label="Username" value={usernameInput} onChange={(e) => setUsernameInput(e.target.value)} />
          <div className="mt-3" />
          <Input
            label="Password"
            type="password"
            value={passwordInput}
            onChange={(e) => setPasswordInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") void handleAuth();
            }}
          />
          {isResetMode && (
            <>
              <div className="mt-3" />
              <Input label="Reset token" value={resetTokenInput} onChange={(e) => setResetTokenInput(e.target.value)} />
            </>
          )}
          <div className="mt-4 flex gap-3 flex-wrap">
            {!isResetMode ? (
              <Button onClick={() => void handleAuth()}>{isRegisterMode ? "Register" : "Login"}</Button>
            ) : (
              <Button onClick={() => void handleResetConfirm()}>Confirm Reset</Button>
            )}
            <Button variant="secondary" onClick={() => setIsRegisterMode((v) => !v)} disabled={isResetMode}>
              {isRegisterMode ? "Switch to Login" : "Switch to Register"}
            </Button>
            <Button variant="secondary" onClick={() => setIsResetMode((v) => !v)}>
              {isResetMode ? "Back Auth" : "Reset Password"}
            </Button>
            {isResetMode && (
              <Button variant="accent" onClick={() => void handleResetRequest()}>
                Get Token
              </Button>
            )}
          </div>
          {statusMessage && <p className="mt-3 font-mono text-xs text-electric-green">{statusMessage}</p>}
          {error && <p className="mt-3 font-mono text-xs text-electric-orange">{error}</p>}
        </Card>
      </main>
    );
  }

  return (
    <main className="min-h-screen p-4 md:p-8">
      <motion.header className="mb-8" style={{ y: heroY, opacity: heroOpacity }}>
        <div className="flex flex-wrap gap-3 items-center justify-between">
          <div>
            <h1 className="text-4xl md:text-5xl font-display font-black text-white mb-2">
              E<span className="text-electric-violet">C</span>H<span className="text-electric-green">O</span>
            </h1>
            <p className="font-mono text-textMuted text-sm">Emotional Chronicle Helping Observations</p>
          </div>
          <div className="flex gap-2 flex-wrap">
            <Link href="/" className="px-3 py-2 border-2 border-white rounded font-mono text-xs hover:bg-white hover:text-black transition-all">
              Dashboard
            </Link>
            <Link href="/notes" className="px-3 py-2 border-2 border-electric-violet rounded font-mono text-xs text-electric-violet hover:bg-electric-violet hover:text-black transition-all">
              Notes
            </Link>
            <Link href="/insights" className="px-3 py-2 border-2 border-electric-green rounded font-mono text-xs text-electric-green hover:bg-electric-green hover:text-black transition-all">
              Insights
            </Link>
            <Button variant="secondary" size="sm" onClick={() => void handleLogout()}>Logout</Button>
          </div>
        </div>
        <p className="mt-3 font-mono text-xs text-electric-cyan">User: {authUser.username}</p>
      </motion.header>

      <BentoGrid className="mb-8">
        <BentoItem span={2} variant="accent" accentColor="violet">
          <div className="p-6">
            <h2 className="font-display text-lg mb-4 flex items-center gap-2">
              <span className="text-electric-violet">◈</span> New Entry
            </h2>
            <textarea
              value={journalEntry}
              onChange={(e) => setJournalEntry(e.target.value)}
              placeholder="What's on your mind? Pour it out..."
              className="w-full h-28 md:h-36 bg-surface border-2 border-borderMuted rounded-md p-3 md:p-4 font-mono text-sm text-text placeholder:text-textMuted focus:outline-none focus:border-electric-violet transition-all duration-150 resize-none"
            />
            <div className="mt-4 flex gap-3 flex-wrap">
              <Button variant="primary" onClick={() => void handleAnalyze()} disabled={isLoading || !journalEntry.trim()}>
                {isLoading ? "Analyzing..." : "Analyze + Save"}
              </Button>
              <Button variant="secondary" onClick={() => void handleSaveDraft()} disabled={!journalEntry.trim()}>
                Save Draft
              </Button>
              <Link href="/notes" className="px-4 py-3 border-2 border-electric-cyan rounded-md font-display text-xs uppercase tracking-wider text-electric-cyan hover:bg-electric-cyan hover:text-black transition-all">
                Open Notes
              </Link>
            </div>
            {statusMessage && <p className="mt-2 font-mono text-xs text-electric-green">{statusMessage}</p>}
            {error && <p className="mt-2 font-mono text-xs text-electric-orange">⚠ {error}</p>}
          </div>
        </BentoItem>

        {emilyResponse && (
          <BentoItem span={2} variant="accent" accentColor={responseAccent}>
            <div className="p-6">
              <h2 className="font-display text-lg mb-4 flex items-center gap-2">
                <span className={responseDotClass}>◈</span> Emily&apos;s Response
              </h2>
              <div className="bg-surface border border-borderMuted rounded p-4 font-mono text-sm text-text">
                {emilyResponse.response.text}
              </div>
              {isFallbackResponse && (
                <div className="mt-2 inline-block px-2 py-1 border border-electric-orange text-electric-orange font-mono text-xs rounded">
                  FALLBACK MODE
                </div>
              )}
              {emotionState && (
                <div className="mt-3 flex flex-wrap gap-4 font-mono text-xs">
                  <div>
                    <span className="text-textMuted">Valence:</span>{" "}
                    <span className={emotionState.emotional_valence < 0 ? "text-electric-orange" : "text-electric-green"}>
                      {emotionState.emotional_valence.toFixed(2)}
                    </span>
                  </div>
                  <div>
                    <span className="text-textMuted">Activation:</span>{" "}
                    <span className="text-electric-violet">{emotionState.activation_level}</span>
                  </div>
                  <div>
                    <span className="text-textMuted">Stability:</span>{" "}
                    <span className="text-electric-pink">{emotionState.stability}</span>
                  </div>
                </div>
              )}
            </div>
          </BentoItem>
        )}

        <BentoItem span={1}>
          <div className="p-6">
            <h2 className="font-display text-lg mb-4 flex items-center gap-2">
              <span className="text-electric-green">◈</span> Mood Check
            </h2>
            <div className="grid grid-cols-2 gap-2">
              {moods.map((m) => (
                <button
                  key={m.label}
                  onClick={() => setMood(m.label)}
                  className={`p-3 rounded-md border-2 font-mono text-xs uppercase transition-all duration-150 ${
                    mood === m.label ? "bg-white text-black border-white shadow-hard" : "bg-surface text-textMuted border-borderMuted hover:border-white"
                  }`}
                >
                  <span className="text-xl block mb-1">{m.emoji}</span>
                  {m.label}
                </button>
              ))}
            </div>
          </div>
        </BentoItem>

        <BentoItem span={1} variant="accent" accentColor="green">
          <div className="p-6">
            <h2 className="font-display text-lg mb-4 flex items-center gap-2">
              <span className="text-electric-green">◈</span> Snapshot
            </h2>
            <div className="space-y-3 font-mono text-sm">
              <div className="flex justify-between items-center"><span className="text-textMuted">Entries</span><span className="text-electric-green font-bold">{entries.length}</span></div>
              <div className="flex justify-between items-center"><span className="text-textMuted">Drafts</span><span className="text-electric-cyan font-bold">{draftCount}</span></div>
              <div className="flex justify-between items-center"><span className="text-textMuted">Avg Mood</span><span className="text-electric-violet font-bold">{toMoodLabel(entries)}</span></div>
            </div>
          </div>
        </BentoItem>

        <BentoItem span={2}>
          <div className="p-6">
            <h2 className="font-display text-lg mb-4 flex items-center gap-2">
              <span className="text-electric-pink">◈</span> Live Insights
            </h2>
            <div className="space-y-3">
              {insights.map((item) => (
                <div key={item} className="bg-surface border border-borderMuted rounded p-3 font-mono text-xs">
                  <span className="text-electric-pink">[INSIGHT]</span> {item}
                </div>
              ))}
            </div>
          </div>
        </BentoItem>

        <BentoItem span={2} variant="accent" accentColor="orange">
          <div className="p-6">
            <h2 className="font-display text-lg mb-4 flex items-center gap-2">
              <span className="text-electric-orange">◈</span> Triggers
            </h2>
            <div className="flex flex-wrap gap-2">
              {triggerCounts.length === 0 ? (
                <span className="font-mono text-xs text-textMuted">No trigger data yet.</span>
              ) : (
                triggerCounts.map(([name, count]) => (
                  <button
                    key={name}
                    onClick={() => setSelectedTrigger((prev) => (prev === name ? null : name))}
                    className={`px-3 py-1 bg-surface border rounded-full font-mono text-xs ${
                      selectedTrigger === name ? "border-white text-white" : "border-electric-orange text-electric-orange"
                    }`}
                  >
                    {name} ({count})
                  </button>
                ))
              )}
            </div>
            <p className="mt-4 font-mono text-xs text-textMuted">{selectedTrigger ? `Selected: ${selectedTrigger}` : "Tap trigger for quick focus."}</p>
          </div>
        </BentoItem>
      </BentoGrid>

      <Card className="p-8 border-electric-cyan" variant="accent" accentColor="cyan">
        <div className="flex flex-wrap gap-4 items-center justify-between">
          <div>
            <h2 className="font-display text-2xl mb-2">Server-backed notes active.</h2>
            <p className="font-mono text-textMuted text-sm">Last entry: {entries[0] ? formatLocalDate(entries[0].createdAt) : "none"}</p>
          </div>
          <div className="flex gap-3">
            <Link href="/notes" className="px-4 py-3 border-2 border-electric-violet rounded-md font-display text-xs uppercase tracking-wider text-electric-violet hover:bg-electric-violet hover:text-black transition-all">
              Open Notes Vault
            </Link>
            <Link href="/insights" className="px-4 py-3 border-2 border-electric-green rounded-md font-display text-xs uppercase tracking-wider text-electric-green hover:bg-electric-green hover:text-black transition-all">
              Open Insights Lab
            </Link>
          </div>
        </div>
      </Card>
      <nav className="fixed bottom-3 left-1/2 -translate-x-1/2 md:hidden z-50 bg-card border-2 border-white rounded-xl shadow-hard-sm px-2 py-2 flex gap-2">
        <Link href="/" className="px-3 py-2 font-mono text-xs border border-white rounded">Home</Link>
        <Link href="/notes" className="px-3 py-2 font-mono text-xs border border-electric-violet text-electric-violet rounded">Notes</Link>
        <Link href="/insights" className="px-3 py-2 font-mono text-xs border border-electric-green text-electric-green rounded">Info</Link>
      </nav>
    </main>
  );
}
