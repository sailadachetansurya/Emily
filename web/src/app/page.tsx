"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { BentoGrid, BentoItem } from "@/components/BentoGrid";
import Card from "@/components/Card";
import Button from "@/components/Button";
import type { EmilyResponse, EmotionState } from "@/lib/emily-api";
import {
  analyzeJournal,
  getDrafts,
  getEntries,
  getServerInsights,
  saveDraft,
} from "@/lib/backend-api";
import { buildInsights, formatLocalDate, JournalRecord, toMoodLabel } from "@/lib/user-data";
import { useAuth } from "@/context/AuthContext";

type AccentColor = "violet" | "green" | "orange" | "pink" | "cyan";

export default function Home() {
  const { user } = useAuth();
  
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

  const moods = [
    { label: "Anxious", emoji: "😰" },
    { label: "Sad", emoji: "😔" },
    { label: "Neutral", emoji: "😐" },
    { label: "Good", emoji: "🙂" },
    { label: "Great", emoji: "🤩" },
  ] as const;

  const loadServerData = async () => {
    try {
      const [nextEntries, nextDrafts, insights] = await Promise.all([
        getEntries(),
        getDrafts(),
        getServerInsights()
      ]);
      setEntries(nextEntries);
      setDraftCount(nextDrafts.length);
      setServerInsights(insights);
    } catch (err) {
      console.error("Failed to load server data:", err);
    }
  };

  useEffect(() => {
    if (user) void loadServerData();
  }, [user]);

  const triggerCounts = useMemo(() => {
    const counts = new Map<string, number>();
    for (const entry of entries) {
      const text = entry.text.toLowerCase();
      // simplified naive extraction for display
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

  const responseTextGlowClass = {
    violet: "text-glow-violet text-neon-violet",
    green: "text-glow-green text-neon-green",
    orange: "text-glow-orange text-neon-orange",
    pink: "text-glow-pink text-neon-pink",
    cyan: "text-glow-cyan text-neon-cyan",
  }[responseAccent];

  const handleAnalyze = async () => {
    if (!user || !journalEntry.trim()) return;
    setIsLoading(true);
    setError(null);
    setStatusMessage("");

    try {
      const response = await analyzeJournal({
        request_id: `req-${Date.now()}`,
        user_id: user.username,
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
          : "Analyzed and auto-saved to server."
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

  if (!user) return null; // handled by AuthGate

  return (
    <main className="p-4 md:p-8 lg:p-12 max-w-[1600px] mx-auto">
      {/* Header */}
      <motion.header 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10 lg:mb-14"
      >
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
          <div>
            <h1 className="text-5xl md:text-7xl font-display font-black tracking-tighter text-white mb-2 text-glow-violet">
              ECHO
            </h1>
            <p className="font-mono text-text-muted text-sm tracking-wider uppercase">
              Emotional Chronicle · Helping Observations
            </p>
          </div>
          <div className="flex gap-3">
            <Link href="/notes">
              <Button variant="secondary" icon="✦">Vault</Button>
            </Link>
            <Link href="/insights">
              <Button variant="accent" icon="◉">Insights</Button>
            </Link>
          </div>
        </div>
      </motion.header>

      {/* Main Grid */}
      <BentoGrid className="mb-10">
        
        {/* Composer Card */}
        <BentoItem span={2} accent="violet" glow>
          <div className="p-8 h-full flex flex-col">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded bg-neon-violet/10 border border-neon-violet/30 flex items-center justify-center text-neon-violet">
                ◈
              </div>
              <h2 className="font-display text-xl font-bold">New Entry</h2>
            </div>
            
            <textarea
              value={journalEntry}
              onChange={(e) => setJournalEntry(e.target.value)}
              placeholder="What's on your mind? Pour it out..."
              className="flex-1 min-h-[140px] w-full bg-bg-surface border-2 border-border-subtle rounded-brutal-sm p-5 font-mono text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-neon-violet focus:shadow-[0_0_0_4px_rgba(139,92,246,0.12)] transition-all resize-none mb-6"
            />
            
            <div className="flex flex-wrap items-center gap-4">
              <Button 
                variant="primary" 
                onClick={() => void handleAnalyze()} 
                disabled={isLoading || !journalEntry.trim()}
                icon={isLoading ? "⟳" : "⚡"}
              >
                {isLoading ? "Analyzing..." : "Analyze + Save"}
              </Button>
              <Button 
                variant="secondary" 
                onClick={() => void handleSaveDraft()} 
                disabled={!journalEntry.trim()}
                icon="⚑"
              >
                Save Draft
              </Button>
            </div>
            
            {/* Feedback messages */}
            {statusMessage && (
              <motion.p initial={{opacity:0}} animate={{opacity:1}} className="mt-4 font-mono text-xs text-neon-green flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-neon-green animate-pulse" /> {statusMessage}
              </motion.p>
            )}
            {error && (
              <motion.p initial={{opacity:0}} animate={{opacity:1}} className="mt-4 font-mono text-xs text-neon-orange flex items-center gap-2">
                <span>⚠</span> {error}
              </motion.p>
            )}
          </div>
        </BentoItem>

        {/* Emily's Response Card - Dynamic inclusion */}
        {emilyResponse && (
          <BentoItem span={isFallbackResponse ? 1 : 2} accent={responseAccent} glow>
            <div className="p-8 h-full flex flex-col">
              <div className="flex items-center gap-3 mb-6">
                <div className={`w-8 h-8 rounded bg-neon-${responseAccent}/10 border border-neon-${responseAccent}/30 flex items-center justify-center text-neon-${responseAccent} animate-glow-pulse`}>
                  ◈
                </div>
                <h2 className="font-display text-xl font-bold">Emily</h2>
              </div>
              
              <div className="flex-1 bg-bg-surface border-2 border-border-subtle rounded-brutal-sm p-5 font-mono text-sm text-text-primary shadow-inner-glow leading-relaxed">
                {emilyResponse.response.text}
              </div>
              
              <div className="mt-6 flex flex-wrap gap-2">
                {isFallbackResponse && (
                  <span className="neon-badge neon-badge-orange">Fallback Mode</span>
                )}
                {emotionState && (
                  <>
                    <span className={`neon-badge neon-badge-${emotionState.emotional_valence < 0 ? 'orange' : 'green'}`}>
                      Valence: {emotionState.emotional_valence.toFixed(2)}
                    </span>
                    <span className="neon-badge neon-badge-violet">
                      {emotionState.activation_level} activation
                    </span>
                  </>
                )}
              </div>
            </div>
          </BentoItem>
        )}

        {/* Mood Check */}
        <BentoItem span={1}>
          <div className="p-8 h-full flex flex-col">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded bg-neon-green/10 border border-neon-green/30 flex items-center justify-center text-neon-green">
                ◉
              </div>
              <h2 className="font-display text-xl font-bold">Mood</h2>
            </div>
            
            <div className="grid grid-cols-2 gap-3 flex-1">
              {moods.map((m) => {
                const isActive = mood === m.label;
                return (
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    key={m.label}
                    onClick={() => setMood(m.label)}
                    className={`
                      flex flex-col items-center justify-center p-4 rounded-brutal-sm border-2 
                      font-mono text-xs uppercase tracking-wider transition-all
                      ${isActive 
                        ? "bg-neon-green border-neon-green text-black shadow-brutal hover:shadow-brutal" 
                        : "bg-bg-surface border-border-subtle text-text-secondary hover:border-border-hard hover:text-text-primary"
                      }
                    `}
                  >
                    <span className="text-3xl mb-2 filter drop-shadow-sm">{m.emoji}</span>
                    {m.label}
                  </motion.button>
                );
              })}
            </div>
          </div>
        </BentoItem>

        {/* Stats Snapshot */}
        <BentoItem span={1} accent="cyan">
          <div className="p-8 h-full flex flex-col">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded bg-neon-cyan/10 border border-neon-cyan/30 flex items-center justify-center text-neon-cyan">
                ◒
              </div>
              <h2 className="font-display text-xl font-bold">Snapshot</h2>
            </div>
            
            <div className="flex-1 flex flex-col justify-center space-y-4 font-mono">
              <div className="flex justify-between items-center p-3 border-2 border-border-subtle rounded-brutal-sm bg-bg-surface hover:border-neon-cyan transition-colors">
                <span className="text-text-secondary text-sm">Total Entries</span>
                <span className="text-neon-cyan font-bold text-lg">{entries.length}</span>
              </div>
              <div className="flex justify-between items-center p-3 border-2 border-border-subtle rounded-brutal-sm bg-bg-surface hover:border-neon-violet transition-colors">
                <span className="text-text-secondary text-sm">Drafts</span>
                <span className="text-neon-violet font-bold text-lg">{draftCount}</span>
              </div>
              <div className="flex justify-between items-center p-3 border-2 border-border-subtle rounded-brutal-sm bg-bg-surface hover:border-neon-green transition-colors">
                <span className="text-text-secondary text-sm">Avg Mood</span>
                <span className="text-neon-green font-bold uppercase">{toMoodLabel(entries)}</span>
              </div>
            </div>
          </div>
        </BentoItem>

        {/* Live Insights */}
        <BentoItem span={2} accent="pink">
          <div className="p-8 h-full flex flex-col">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded bg-neon-pink/10 border border-neon-pink/30 flex items-center justify-center text-neon-pink">
                ✦
              </div>
              <h2 className="font-display text-xl font-bold">Live Insights</h2>
            </div>
            
            <div className="flex-1 space-y-4">
              {insights.map((item, idx) => (
                <motion.div 
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: idx * 0.1 }}
                  key={item} 
                  className="bg-bg-surface border-2 border-border-subtle rounded-brutal-sm p-4 font-mono text-sm flex gap-3 hover:border-neon-pink/50 transition-colors"
                >
                  <span className="text-neon-pink shrink-0">◇</span> 
                  <span className="text-text-primary">{item}</span>
                </motion.div>
              ))}
            </div>
          </div>
        </BentoItem>

        {/* Triggers */}
        <BentoItem span={triggerCounts.length === 0 ? 1 : 2} accent="orange">
          <div className="p-8 h-full flex flex-col">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-8 h-8 rounded bg-neon-orange/10 border border-neon-orange/30 flex items-center justify-center text-neon-orange">
                ◬
              </div>
              <h2 className="font-display text-xl font-bold">Triggers</h2>
            </div>
            
            {triggerCounts.length === 0 ? (
              <div className="flex-1 flex items-center justify-center border-2 border-dashed border-border-subtle rounded-brutal-sm font-mono text-sm text-text-muted p-6 text-center">
                No trigger patterns identified yet. Keep journaling.
              </div>
            ) : (
              <div className="flex-1 flex flex-col">
                <div className="flex flex-wrap gap-3">
                  {triggerCounts.map(([name, count]) => (
                    <motion.button
                      whileHover={{ y: -2 }}
                      whileTap={{ y: 0 }}
                      key={name}
                      onClick={() => setSelectedTrigger((prev) => (prev === name ? null : name))}
                      className={`
                        px-4 py-2 rounded-brutal-sm border-2 font-mono text-xs uppercase tracking-wider transition-all
                        ${selectedTrigger === name 
                          ? "bg-neon-orange border-neon-orange text-black shadow-brutal-sm" 
                          : "bg-bg-surface border-neon-orange/50 text-neon-orange hover:border-neon-orange"
                        }
                      `}
                    >
                      {name} <span className="opacity-70 ml-1 font-bold">({count})</span>
                    </motion.button>
                  ))}
                </div>
                {selectedTrigger && (
                  <motion.div 
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    className="mt-6 p-4 bg-neon-orange/10 border border-neon-orange/30 rounded-brutal-sm font-mono text-xs text-neon-orange"
                  >
                    Focusing on <strong className="uppercase">{selectedTrigger}</strong>. These entries have a higher emotional activation cost.
                  </motion.div>
                )}
              </div>
            )}
          </div>
        </BentoItem>

      </BentoGrid>

      {/* Footer Banner */}
      <Card className="p-8" accent="none">
        <div className="flex flex-col md:flex-row gap-6 items-center justify-between">
          <div>
            <h2 className="font-display text-2xl font-bold mb-2">Your Emotional Data is Secured.</h2>
            <p className="font-mono text-text-muted text-sm">
              Last synchronization: {entries[0] ? formatLocalDate(entries[0].createdAt) : "never"}
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link href="/notes">
              <Button variant="secondary" icon="⚑">View All Notes</Button>
            </Link>
          </div>
        </div>
      </Card>
      
    </main>
  );
}
