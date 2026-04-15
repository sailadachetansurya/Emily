"use client";

import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import Card from "@/components/Card";
import { getEntries, getServerInsights } from "@/lib/backend-api";
import { JournalRecord, toMoodLabel } from "@/lib/user-data";
import { useAuth } from "@/context/AuthContext";

function triggerMap(entries: JournalRecord[]): Array<{ name: string; count: number }> {
  const counts = new Map<string, number>();
  for (const entry of entries) {
    const text = entry.text.toLowerCase();
    for (const token of ["work", "social", "night", "money", "family", "friend"]) {
      if (text.includes(token)) counts.set(token, (counts.get(token) ?? 0) + 1);
    }
  }
  return Array.from(counts.entries())
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);
}

export default function InsightsPage() {
  const { user } = useAuth();
  const [entries, setEntries] = useState<JournalRecord[]>([]);
  const [insights, setInsights] = useState<string[]>([]);
  
  const triggers = useMemo(() => triggerMap(entries), [entries]);

  const loadData = async () => {
    try {
      const [nextEntries, nextInsights] = await Promise.all([getEntries(), getServerInsights()]);
      setEntries(nextEntries);
      setInsights(nextInsights);
    } catch(err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (user) void loadData();
  }, [user]);

  if (!user) return null;

  return (
    <main className="p-4 md:p-8 lg:p-12 max-w-[1200px] mx-auto">
      <motion.header 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10 lg:mb-14"
      >
        <h1 className="text-4xl md:text-5xl font-display font-black tracking-tighter text-white mb-2 text-glow-green">
          INSIGHTS LAB
        </h1>
        <p className="font-mono text-text-muted text-sm tracking-wider uppercase">
          Behavioral signals and patterns
        </p>
      </motion.header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Behavior Signals */}
        <motion.div
           initial={{ opacity: 0, scale: 0.95 }}
           animate={{ opacity: 1, scale: 1 }}
           transition={{ delay: 0.1 }}
           className="lg:col-span-2"
        >
          <Card className="h-full flex flex-col" accent="green" label="BEHAVIOR_SIGNALS">
            <div className="p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded bg-neon-green/10 border border-neon-green/30 flex items-center justify-center text-neon-green">
                  ◉
                </div>
                <h2 className="font-display text-xl font-bold">Behavior Signals</h2>
              </div>

              <div className="space-y-4">
                {insights.length === 0 && (
                  <div className="border border-dashed border-border-subtle rounded-brutal-sm p-6 text-center text-text-muted font-mono text-sm">
                    No signals detected yet. Add more data.
                  </div>
                )}
                {insights.map((insight, idx) => (
                  <motion.div 
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 + idx * 0.1 }}
                    key={insight} 
                    className="bg-bg-surface border-2 border-border-subtle rounded-brutal-sm p-5 font-mono text-sm flex gap-4 hover:border-neon-green transition-colors items-start"
                  >
                    <span className="text-neon-green text-lg shrink-0 mt-[-2px]">↳</span>
                    <span className="text-text-primary leading-relaxed">{insight}</span>
                  </motion.div>
                ))}
              </div>
            </div>
          </Card>
        </motion.div>

        {/* Quick Metrics & Top Triggers */}
        <motion.div
           initial={{ opacity: 0, scale: 0.95 }}
           animate={{ opacity: 1, scale: 1 }}
           transition={{ delay: 0.2 }}
           className="flex flex-col gap-6"
        >
          {/* Metrics */}
          <Card accent="cyan" label="METRIC_STACK">
            <div className="p-8">
              <div className="flex items-center gap-3 mb-6">
                 <div className="w-8 h-8 rounded bg-neon-cyan/10 border border-neon-cyan/30 flex items-center justify-center text-neon-cyan">
                   ◒
                 </div>
                 <h2 className="font-display text-xl font-bold">Metrics</h2>
              </div>

              <div className="space-y-3 font-mono text-sm">
                <div className="flex justify-between items-center p-3 bg-bg-surface border border-border-subtle rounded-brutal-sm">
                  <span className="text-text-secondary">Entries Analyzed</span>
                  <span className="text-neon-cyan font-bold">{entries.length}</span>
                </div>
                <div className="flex justify-between items-center p-3 bg-bg-surface border border-border-subtle rounded-brutal-sm">
                  <span className="text-text-secondary">Mood Trend</span>
                  <span className="font-bold text-white uppercase">{toMoodLabel(entries)}</span>
                </div>
              </div>
            </div>
          </Card>

          {/* Triggers */}
          <Card accent="orange" className="flex-1" label="TRIGGER_MAP">
            <div className="p-8">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded bg-neon-orange/10 border border-neon-orange/30 flex items-center justify-center text-neon-orange">
                  ◬
                </div>
                <h2 className="font-display text-xl font-bold">Top Triggers</h2>
              </div>

              <div className="space-y-3">
                {triggers.length === 0 && (
                  <p className="font-mono text-xs text-text-muted">No trigger data.</p>
                )}
                {triggers.map((item, idx) => (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.3 + idx * 0.1 }}
                    key={item.name} 
                    className="flex justify-between items-center font-mono text-sm border-2 border-border-subtle bg-bg-surface rounded-brutal-sm p-3 hover:border-neon-orange transition-colors"
                  >
                    <span className="uppercase font-semibold tracking-wider">{item.name}</span>
                    <span className="text-neon-orange bg-neon-orange/10 px-2 py-0.5 rounded text-xs font-bold w-6 text-center">
                      {item.count}
                    </span>
                  </motion.div>
                ))}
              </div>
            </div>
          </Card>
        </motion.div>

      </div>
    </main>
  );
}
