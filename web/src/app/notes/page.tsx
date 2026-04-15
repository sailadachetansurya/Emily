"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Card from "@/components/Card";
import Button from "@/components/Button";
import {
  deleteEntry,
  deleteDraft,
  getDrafts,
  getEntries,
  updateEntry,
} from "@/lib/backend-api";
import { DraftRecord, formatLocalDate, JournalRecord } from "@/lib/user-data";
import { useAuth } from "@/context/AuthContext";

export default function NotesPage() {
  const { user } = useAuth();
  
  const [entries, setEntries] = useState<JournalRecord[]>([]);
  const [drafts, setDrafts] = useState<DraftRecord[]>([]);
  const [editingEntryId, setEditingEntryId] = useState<string | null>(null);
  const [editingEntryText, setEditingEntryText] = useState("");

  const loadData = async () => {
    try {
      const [nextEntries, nextDrafts] = await Promise.all([getEntries(), getDrafts()]);
      setEntries(nextEntries);
      setDrafts(nextDrafts);
    } catch(err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (user) void loadData();
  }, [user]);

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

  if (!user) return null;

  return (
    <main className="p-4 md:p-8 lg:p-12 max-w-[1600px] mx-auto">
      <motion.header 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-10 lg:mb-14"
      >
        <h1 className="text-4xl md:text-5xl font-display font-black tracking-tighter text-white mb-2 text-glow-cyan">
          NOTES VAULT
        </h1>
        <p className="font-mono text-text-muted text-sm tracking-wider uppercase">
          Your archived emotional records
        </p>
      </motion.header>

      <section className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        {/* Drafts Section */}
        <motion.div
           initial={{ opacity: 0, x: -20 }}
           animate={{ opacity: 1, x: 0 }}
           transition={{ delay: 0.1 }}
        >
          <Card className="h-full flex flex-col" accent="cyan" label="DRAFT_BUFFER">
            <div className="p-8 pb-4">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded bg-neon-cyan/10 border border-neon-cyan/30 flex items-center justify-center text-neon-cyan">
                  ⚑
                </div>
                <h2 className="font-display text-xl font-bold">Drafts ({drafts.length})</h2>
              </div>
            </div>
            
            <div className="flex-1 p-8 pt-0 overflow-y-auto max-h-[70vh] space-y-4">
              {drafts.length === 0 && (
                <div className="border-2 border-dashed border-border-subtle rounded-brutal-sm p-8 text-center text-text-muted font-mono text-sm">
                  No drafts saved.
                </div>
              )}
              <AnimatePresence>
                {drafts.map((draft) => (
                  <motion.div 
                    layout
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95, height: 0, marginBottom: 0 }}
                    key={draft.id} 
                    className="bg-bg-surface border-2 border-border-subtle rounded-brutal-sm p-5 hover:border-border-hard transition-colors group"
                  >
                    <p className="font-mono text-sm text-text-primary whitespace-pre-wrap leading-relaxed mb-4">
                      {draft.text}
                    </p>
                    <div className="flex justify-between items-center pt-4 border-t border-border-subtle/50">
                      <span className="font-mono text-xs text-text-muted">
                        {formatLocalDate(draft.createdAt)}
                      </span>
                      <Button 
                        variant="danger" 
                        size="sm"
                        onClick={() => void removeDraft(draft.id)}
                        className="opacity-0 group-hover:opacity-100 transition-opacity"
                        icon="✕"
                      >
                        Delete
                      </Button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </Card>
        </motion.div>

        {/* Analyzed Notes Section */}
        <motion.div
           initial={{ opacity: 0, x: 20 }}
           animate={{ opacity: 1, x: 0 }}
           transition={{ delay: 0.2 }}
        >
          <Card className="h-full flex flex-col" accent="violet" label="ANALYZE_RECORDS">
            <div className="p-8 pb-4">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded bg-neon-violet/10 border border-neon-violet/30 flex items-center justify-center text-neon-violet">
                  ◈
                </div>
                <h2 className="font-display text-xl font-bold">Analyzed Records ({entries.length})</h2>
              </div>
            </div>

            <div className="flex-1 p-8 pt-0 overflow-y-auto max-h-[70vh] space-y-4">
              {entries.length === 0 && (
                 <div className="border-2 border-dashed border-border-subtle rounded-brutal-sm p-8 text-center text-text-muted font-mono text-sm">
                   No analyzed entries yet.
                 </div>
              )}
              <AnimatePresence>
                {entries.map((entry) => (
                  <motion.div 
                    layout
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95, height: 0, marginBottom: 0 }}
                    key={entry.id} 
                    className="bg-bg-surface border-2 border-border-subtle rounded-brutal-sm p-5 hover:border-border-hard transition-colors group"
                  >
                    <div className="flex justify-between items-start mb-4">
                      <span className="font-mono text-xs text-text-muted">
                        {formatLocalDate(entry.createdAt)}
                      </span>
                      {entry.mood && (
                        <span className="neon-badge neon-badge-violet text-[10px] px-2 py-0.5">
                          {entry.mood}
                        </span>
                      )}
                    </div>
                    
                    {editingEntryId === entry.id ? (
                      <textarea
                        value={editingEntryText}
                        onChange={(e) => setEditingEntryText(e.target.value)}
                        className="w-full h-32 bg-bg-card border-2 border-neon-cyan rounded-brutal-sm p-4 font-mono text-sm text-text-primary focus:outline-none mb-4 resize-none"
                      />
                    ) : (
                      <p className="font-mono text-sm text-text-primary whitespace-pre-wrap leading-relaxed mb-4">
                        {entry.text}
                      </p>
                    )}

                    <div className="bg-neon-green/5 border border-neon-green/20 rounded p-4 mb-4">
                      <p className="font-mono text-xs text-neon-green font-bold mb-1">Emily's Analysis</p>
                      <p className="font-mono text-xs text-text-primary leading-relaxed">{entry.responseText}</p>
                    </div>

                    <div className="flex justify-end gap-2 pt-4 border-t border-border-subtle/50 opacity-100 xl:opacity-0 group-hover:opacity-100 transition-opacity">
                      {editingEntryId === entry.id ? (
                        <>
                          <Button variant="ghost" size="sm" onClick={() => setEditingEntryId(null)}>Cancel</Button>
                          <Button variant="accent" size="sm" onClick={() => void saveEditEntry(entry)}>Save Save</Button>
                        </>
                      ) : (
                        <Button variant="secondary" size="sm" onClick={() => startEditEntry(entry)} icon="✎">Edit</Button>
                      )}
                      
                      <Button variant="danger" size="sm" onClick={() => void removeEntry(entry.id)} icon="✕">Delete</Button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </Card>
        </motion.div>
      </section>
    </main>
  );
}
