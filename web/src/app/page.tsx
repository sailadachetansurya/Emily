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
  const [isLoading, setIsLoading] = useState(false);

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
      console.error("Sync error:", err);
    }
  };

  useEffect(() => {
    if (user) void loadServerData();
  }, [user]);

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

  const handleAnalyze = async () => {
    if (!user || !journalEntry.trim()) return;
    setIsLoading(true);

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
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) return null;

  return (
    <main className="p-4 md:p-8 lg:p-12 max-w-[1600px] mx-auto bg-bg-primary">
      {/* ── HEADER HUD ── */}
      <header className="mb-12 border-b-4 border-white pb-6 flex flex-col md:flex-row justify-between items-end gap-6">
        <div>
          <div className="flex items-center gap-4 mb-2">
            <h1 className="text-6xl md:text-8xl font-display font-black tracking-tighter text-white">
              ECHO<span className="text-neon-violet">.</span>OS
            </h1>
            <div className="bg-neon-green px-2 py-1 text-black font-display text-[10px] font-black">
              V0.2.0-STABLE
            </div>
          </div>
          <p className="hud-text">
            SYSTEM_STATUS: <span className="text-neon-green">ENCRYPTION_ACTIVE</span> // USER: <span className="text-white">{user.username.toUpperCase()}</span>
          </p>
        </div>
        <div className="flex gap-4">
          <Link href="/notes">
            <Button variant="secondary" size="sm">VAULT_ARCHIVE</Button>
          </Link>
          <Link href="/insights">
            <Button variant="accent" size="sm">NEURAL_DECODE</Button>
          </Link>
        </div>
      </header>

      {/* ── MAIN TERMINAL GRID ── */}
      <BentoGrid>
        
        {/* INPUT TERMINAL */}
        <BentoItem span={2} label="EMOTIVE_INPUT_BUFFER" accent="violet">
            <div className="flex flex-col h-full">
              <textarea
                value={journalEntry}
                onChange={(e) => setJournalEntry(e.target.value)}
                placeholder="PROMPT: RECORD_CURRENT_STATE..."
                className="w-full h-48 bg-black border-4 border-white p-6 font-mono text-sm text-neon-violet placeholder:text-zinc-800 focus:outline-none focus:border-neon-violet transition-colors mb-6"
              />
              <div className="flex gap-4">
                <Button 
                  variant="primary" 
                  onClick={() => void handleAnalyze()} 
                  disabled={isLoading || !journalEntry.trim()}
                  fullWidth
                >
                  {isLoading ? "ANALYZING_FLUX..." : "EXECUTE_ANALYSIS"}
                </Button>
                <Button 
                  variant="secondary" 
                  onClick={() => {
                    if (journalEntry.trim()) {
                      saveDraft(journalEntry, mood);
                      setJournalEntry("");
                    }
                  }}
                  disabled={!journalEntry.trim()}
                >
                  SAVE_DRAFT
                </Button>
              </div>
            </div>
        </BentoItem>

        {/* EMILY RESPONSE LOG */}
        <BentoItem span={2} label="EMILY_NEURAL_LOG" accent="green">
             {!emilyResponse ? (
               <div className="flex flex-col items-center justify-center h-48 border-4 border-dashed border-zinc-900">
                  <p className="hud-text text-zinc-800">AWAITING_INPUT_FOR_LOG_GENERATION</p>
               </div>
             ) : (
               <div className="flex flex-col h-full">
                  <div className="flex-1 bg-zinc-950 border-4 border-white p-6 font-mono text-sm text-white border-l-neon-green leading-relaxed">
                    <span className="text-neon-green mb-4 block font-black">&gt; EMILY:</span>
                    {emilyResponse.response.text}
                  </div>
                  
                  {emotionState && (
                    <div className="mt-6 grid grid-cols-3 gap-4">
                      <div className="border-2 border-white p-2">
                        <p className="hud-text text-[8px]">VALENCE</p>
                        <p className={`font-display font-black text-xs ${emotionState.emotional_valence < 0 ? 'text-neon-orange' : 'text-neon-green'}`}>
                          {emotionState.emotional_valence.toFixed(4)}
                        </p>
                      </div>
                      <div className="border-2 border-white p-2">
                        <p className="hud-text text-[8px]">ACTIVATION</p>
                        <p className="font-display font-black text-xs text-neon-violet">
                          {emotionState.activation_level.toUpperCase()}
                        </p>
                      </div>
                      <div className="border-2 border-white p-2">
                        <p className="hud-text text-[8px]">STABILITY</p>
                        <p className="font-display font-black text-xs text-neon-cyan">
                          {emotionState.stability.toUpperCase()}
                        </p>
                      </div>
                    </div>
                  )}
               </div>
             )}
        </BentoItem>

        {/* MOOD MATRIX */}
        <BentoItem span={1} label="MOOD_MATRIX">
            <div className="grid grid-cols-2 gap-4">
              {["Anxious", "Sad", "Neutral", "Good", "Great"].map((m) => (
                <button
                  key={m}
                  onClick={() => setMood(m)}
                  className={`
                    p-4 border-4 font-display font-black text-[10px] tracking-tighter flex flex-col items-center justify-center transition-all
                    ${mood === m 
                      ? "bg-neon-green border-neon-green text-black scale-95" 
                      : "bg-black border-white text-white hover:border-neon-green"
                    }
                  `}
                >
                  <span className="text-2xl mb-1">{
                    m === "Anxious" ? "😰" : m === "Sad" ? "😔" : m === "Neutral" ? "😐" : m === "Good" ? "🙂" : "🤩"
                  }</span>
                  {m.toUpperCase()}
                </button>
              ))}
            </div>
        </BentoItem>

        {/* TRIGGER DECODE */}
        <BentoItem span={2} label="TRIGGER_DECODE_MAP" accent="orange">
              <div className="flex flex-wrap gap-4">
                {triggerCounts.length === 0 ? (
                  <p className="hud-text p-10 w-full text-center">NO_TRIGGER_PATTERNS_DETECTED</p>
                ) : (
                  triggerCounts.map(([name, count]) => (
                    <button
                      key={name}
                      onClick={() => setSelectedTrigger(selectedTrigger === name ? null : name)}
                      className={`
                        px-6 py-4 border-4 font-display font-black text-xs transition-all
                        ${selectedTrigger === name 
                          ? "bg-neon-orange border-neon-orange text-black translate-x-1 translate-y-1" 
                          : "bg-black border-white text-neon-orange hover:bg-zinc-900"
                        }
                      `}
                    >
                      {name.toUpperCase()} [{count}]
                    </button>
                  ))
                )}
              </div>
        </BentoItem>

        {/* SYSTEM STATS */}
        <BentoItem span={1}>
          <Card label="SYSTEM_SNAPSHOT">
            <div className="space-y-4 font-display font-black text-xs">
              <div className="flex justify-between border-b-2 border-zinc-900 pb-2">
                <span className="text-zinc-600">ENTRIES:</span>
                <span>{entries.length}</span>
              </div>
              <div className="flex justify-between border-b-2 border-zinc-900 pb-2">
                <span className="text-zinc-600">DRAFTS:</span>
                <span>{draftCount}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-zinc-600">MOOD_AVG:</span>
                <span className="text-neon-violet">{toMoodLabel(entries).toUpperCase()}</span>
              </div>
            </div>
          </Card>
        </BentoItem>

      </BentoGrid>

      <footer className="mt-20 border-t-4 border-white pt-6">
        <p className="hud-text text-center">
          ECHO_V0.2.0 // POWERED_BY_EMILY_AI // END_OF_TRANSMISSION
        </p>
      </footer>
    </main>
  );
}
