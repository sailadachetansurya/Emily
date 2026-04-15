"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import Card from "@/components/Card";
import Button from "@/components/Button";
import { Input } from "@/components/Input";
import {
  deleteEntry,
  deleteDraft,
  getDrafts,
  getEntries,
  login,
  logout,
  me,
  register,
  updateEntry,
} from "@/lib/backend-api";
import { DraftRecord, formatLocalDate, JournalRecord } from "@/lib/user-data";

export default function NotesPage() {
  const [authUser, setAuthUser] = useState<{ user_id: string; username: string } | null>(null);
  const [usernameInput, setUsernameInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [entries, setEntries] = useState<JournalRecord[]>([]);
  const [drafts, setDrafts] = useState<DraftRecord[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isHydrating, setIsHydrating] = useState(true);
  const [editingEntryId, setEditingEntryId] = useState<string | null>(null);
  const [editingEntryText, setEditingEntryText] = useState("");

  const loadData = async () => {
    const [nextEntries, nextDrafts] = await Promise.all([getEntries(), getDrafts()]);
    setEntries(nextEntries);
    setDrafts(nextDrafts);
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
    setDrafts([]);
  };

  const removeDraft = async (draftId: string) => {
    await deleteDraft(draftId);
    await loadData();
  };

  const removeEntry = async (entryId: string) => {
    await deleteEntry(entryId);
    await loadData();
  };

  const startEditEntry = (entry: JournalRecord) => {
    setEditingEntryId(entry.id);
    setEditingEntryText(entry.text);
  };

  const saveEditEntry = async (entry: JournalRecord) => {
    if (!editingEntryId) return;
    await updateEntry(editingEntryId, editingEntryText, entry.mood);
    setEditingEntryId(null);
    setEditingEntryText("");
    await loadData();
  };

  if (isHydrating) {
    return <main className="min-h-screen p-8 font-mono text-sm">Loading...</main>;
  }

  if (!authUser) {
    return (
      <main className="min-h-screen p-4 md:p-8 flex items-center justify-center">
        <Card className="w-full max-w-xl p-8 border-electric-violet" variant="accent" accentColor="violet">
          <h1 className="text-3xl font-display mb-2">Notes Vault</h1>
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
          <h1 className="text-3xl font-display">Notes Vault</h1>
          <p className="font-mono text-xs text-textMuted">User: {authUser.username}</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Link href="/" className="px-3 py-2 border-2 border-white rounded font-mono text-xs hover:bg-white hover:text-black transition-all">
            Dashboard
          </Link>
          <Link href="/insights" className="px-3 py-2 border-2 border-electric-green rounded font-mono text-xs text-electric-green hover:bg-electric-green hover:text-black transition-all">
            Insights
          </Link>
          <Button variant="secondary" size="sm" onClick={() => void handleLogout()}>Logout</Button>
        </div>
      </header>

      <section className="grid grid-cols-1 xl:grid-cols-2 gap-4">
        <Card className="p-6 border-electric-cyan" variant="accent" accentColor="cyan">
          <h2 className="font-display text-lg mb-4">Drafts ({drafts.length})</h2>
          <div className="space-y-3 max-h-[65vh] overflow-auto pr-2">
            {drafts.length === 0 && <p className="font-mono text-xs text-textMuted">No drafts yet.</p>}
            {drafts.map((draft) => (
              <div key={draft.id} className="bg-surface border border-borderMuted rounded p-3">
                <p className="font-mono text-sm whitespace-pre-wrap">{draft.text}</p>
                <div className="mt-2 flex justify-between items-center">
                  <span className="font-mono text-xs text-textMuted">{formatLocalDate(draft.createdAt)}</span>
                  <button
                    onClick={() => void removeDraft(draft.id)}
                    className="font-mono text-xs text-electric-orange border border-electric-orange rounded px-2 py-1 hover:bg-electric-orange hover:text-black transition-all"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-6 border-electric-violet" variant="accent" accentColor="violet">
          <h2 className="font-display text-lg mb-4">Analyzed Notes ({entries.length})</h2>
          <div className="space-y-3 max-h-[65vh] overflow-auto pr-2">
            {entries.length === 0 && <p className="font-mono text-xs text-textMuted">No analyzed notes yet.</p>}
            {entries.map((entry) => (
              <div key={entry.id} className="bg-surface border border-borderMuted rounded p-3">
                <p className="font-mono text-xs text-textMuted">{formatLocalDate(entry.createdAt)}</p>
                {editingEntryId === entry.id ? (
                  <textarea
                    value={editingEntryText}
                    onChange={(e) => setEditingEntryText(e.target.value)}
                    className="w-full mt-2 h-24 bg-background border border-borderMuted rounded p-2 font-mono text-sm"
                  />
                ) : (
                  <p className="font-mono text-sm mt-2 whitespace-pre-wrap">{entry.text}</p>
                )}
                <p className="font-mono text-xs mt-2 text-electric-green">Emily: {entry.responseText}</p>
                <div className="mt-2 flex gap-2">
                  {editingEntryId === entry.id ? (
                    <button
                      onClick={() => void saveEditEntry(entry)}
                      className="font-mono text-xs text-electric-green border border-electric-green rounded px-2 py-1 hover:bg-electric-green hover:text-black transition-all"
                    >
                      Save
                    </button>
                  ) : (
                    <button
                      onClick={() => startEditEntry(entry)}
                      className="font-mono text-xs text-electric-cyan border border-electric-cyan rounded px-2 py-1 hover:bg-electric-cyan hover:text-black transition-all"
                    >
                      Edit
                    </button>
                  )}
                  <button
                    onClick={() => void removeEntry(entry.id)}
                    className="font-mono text-xs text-electric-orange border border-electric-orange rounded px-2 py-1 hover:bg-electric-orange hover:text-black transition-all"
                  >
                    Delete
                  </button>
                </div>
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
