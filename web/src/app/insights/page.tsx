"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import Card from "@/components/Card";
import Button from "@/components/Button";
import { Input } from "@/components/Input";
import { getEntries, getServerInsights, login, logout, me, register } from "@/lib/backend-api";
import { JournalRecord, toMoodLabel } from "@/lib/user-data";

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
  const [authUser, setAuthUser] = useState<{ user_id: string; username: string } | null>(null);
  const [usernameInput, setUsernameInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [entries, setEntries] = useState<JournalRecord[]>([]);
  const [insights, setInsights] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isHydrating, setIsHydrating] = useState(true);

  const triggers = useMemo(() => triggerMap(entries), [entries]);

  const loadData = async () => {
    const [nextEntries, nextInsights] = await Promise.all([getEntries(), getServerInsights()]);
    setEntries(nextEntries);
    setInsights(nextInsights);
  };

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const user = await me();
        setAuthUser(user);
        setUsernameInput(user.username);
        await loadData();
      } catch {
        setAuthUser(null);
      } finally {
        setIsHydrating(false);
      }
    };
    void bootstrap();
  }, []);

  const handleAuth = async () => {
    try {
      const user = isRegisterMode
        ? await register(usernameInput.trim().toLowerCase(), passwordInput)
        : await login(usernameInput.trim().toLowerCase(), passwordInput);
      setAuthUser(user);
      setPasswordInput("");
      await loadData();
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Auth failed");
    }
  };

  const handleLogout = async () => {
    await logout();
    setAuthUser(null);
    setEntries([]);
    setInsights([]);
  };

  if (isHydrating) {
    return <main className="min-h-screen p-8 font-mono text-sm">Loading...</main>;
  }

  if (!authUser) {
    return (
      <main className="min-h-screen p-4 md:p-8 flex items-center justify-center">
        <Card className="w-full max-w-xl p-8 border-electric-violet" variant="accent" accentColor="violet">
          <h1 className="text-3xl font-display mb-2">Insights Lab</h1>
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
          <div className="mt-4 flex gap-3">
            <Button onClick={() => void handleAuth()}>{isRegisterMode ? "Register" : "Login"}</Button>
            <Button variant="secondary" onClick={() => setIsRegisterMode((v) => !v)}>
              {isRegisterMode ? "Switch to Login" : "Switch to Register"}
            </Button>
          </div>
          {error && <p className="mt-3 font-mono text-xs text-electric-orange">{error}</p>}
        </Card>
      </main>
    );
  }

  return (
    <main className="min-h-screen p-4 md:p-8">
      <header className="mb-8 flex flex-wrap gap-3 justify-between items-center">
        <div>
          <h1 className="text-3xl font-display">Insights Lab</h1>
          <p className="font-mono text-xs text-textMuted">User: {authUser.username}</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Link href="/" className="px-3 py-2 border-2 border-white rounded font-mono text-xs hover:bg-white hover:text-black transition-all">
            Dashboard
          </Link>
          <Link href="/notes" className="px-3 py-2 border-2 border-electric-violet rounded font-mono text-xs text-electric-violet hover:bg-electric-violet hover:text-black transition-all">
            Notes
          </Link>
          <Button variant="secondary" size="sm" onClick={() => void handleLogout()}>Logout</Button>
        </div>
      </header>

      <section className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <Card className="p-6 border-electric-green xl:col-span-2" variant="accent" accentColor="green">
          <h2 className="font-display text-lg mb-4">Behavior Signals</h2>
          <div className="space-y-3">
            {insights.length === 0 && <div className="font-mono text-xs text-textMuted">No insights yet.</div>}
            {insights.map((insight) => (
              <div key={insight} className="bg-surface border border-borderMuted rounded p-3 font-mono text-xs">
                {insight}
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-6 border-electric-orange" variant="accent" accentColor="orange">
          <h2 className="font-display text-lg mb-4">Quick Metrics</h2>
          <div className="space-y-2 font-mono text-sm">
            <div className="flex justify-between"><span className="text-textMuted">Entries</span><span>{entries.length}</span></div>
            <div className="flex justify-between"><span className="text-textMuted">Mood trend</span><span>{toMoodLabel(entries)}</span></div>
            <div className="flex justify-between"><span className="text-textMuted">Trigger types</span><span>{triggers.length}</span></div>
          </div>
          <h3 className="font-display text-sm mt-6 mb-2">Top Triggers</h3>
          <div className="space-y-2">
            {triggers.length === 0 && <p className="font-mono text-xs text-textMuted">No trigger data.</p>}
            {triggers.map((item) => (
              <div key={item.name} className="flex justify-between font-mono text-xs border border-borderMuted rounded p-2">
                <span>{item.name}</span>
                <span className="text-electric-orange">{item.count}</span>
              </div>
            ))}
          </div>
        </Card>
      </section>
      <nav className="fixed bottom-3 left-1/2 -translate-x-1/2 md:hidden z-50 bg-card border-2 border-white rounded-xl shadow-hard-sm px-2 py-2 flex gap-2">
        <Link href="/" className="px-3 py-2 font-mono text-xs border border-white rounded">Home</Link>
        <Link href="/notes" className="px-3 py-2 font-mono text-xs border border-electric-violet text-electric-violet rounded">Notes</Link>
        <Link href="/insights" className="px-3 py-2 font-mono text-xs border border-electric-green text-electric-green rounded">Info</Link>
      </nav>
    </main>
  );
}
