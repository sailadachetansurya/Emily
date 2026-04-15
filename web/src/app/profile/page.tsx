"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import Card from "@/components/Card";
import Button from "@/components/Button";
import { getProfile, updateProfile } from "@/lib/backend-api";
import { useAuth } from "@/context/AuthContext";

export default function ProfilePage() {
  const { user } = useAuth();
  const [about, setAbout] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const loadProfile = async () => {
    try {
      const data = await getProfile();
      setAbout(data.about);
    } catch(err) {
      console.error(err);
    }
  };

  useEffect(() => {
    if (user) void loadProfile();
  }, [user]);

  const handleSave = async () => {
    setIsLoading(true);
    try {
      await updateProfile(about);
      setIsEditing(false);
    } catch(err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  if (!user) return null;

  return (
    <main className="p-4 md:p-8 lg:p-12 max-w-[1200px] mx-auto bg-bg-primary">
      <header className="mb-12 flex flex-col md:flex-row justify-between items-end gap-6 border-b-4 border-white pb-6">
        <div>
          <h1 className="text-4xl md:text-5xl font-display font-black tracking-tighter text-white mb-2 text-glow-pink">
            USER_IDENTITY <span className="text-neon-pink text-xs relative top-[-20px] bg-neon-pink/20 px-2 py-1">V_1.0</span>
          </h1>
          <p className="hud-text">
            IDENTIFIER: <span className="text-neon-pink">{user.username.toUpperCase()}</span>
          </p>
        </div>
      </header>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Profile Card */}
        <motion.div
           initial={{ opacity: 0, scale: 0.95 }}
           animate={{ opacity: 1, scale: 1 }}
        >
          <Card className="h-full flex flex-col" accent="pink" label="IDENTITY_MATRIX">
            <div className="flex flex-col h-full space-y-6">
              <div className="flex items-center gap-6">
                <div className="w-24 h-24 bg-neon-pink text-black font-display font-black flex items-center justify-center text-5xl shadow-[8px_8px_0_0_#fff] border-4 border-black border-rotate">
                  {user.username.charAt(0).toUpperCase()}
                </div>
                <div>
                  <h2 className="font-display text-2xl uppercase tracking-wider">{user.username}</h2>
                  <p className="font-mono text-neon-pink text-xs mt-1">STATUS: ONLINE</p>
                </div>
              </div>

              <div className="border-t-4 border-zinc-900 pt-6 flex-1 flex flex-col">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="hud-text text-white">BIOMETRIC_DATA (ABOUT)</h3>
                  {!isEditing && (
                    <Button variant="secondary" size="sm" onClick={() => setIsEditing(true)}>EDIT</Button>
                  )}
                </div>

                {isEditing ? (
                  <div className="flex flex-col flex-1 gap-4">
                    <textarea
                      value={about}
                      onChange={(e) => setAbout(e.target.value)}
                      placeholder="ENTER CORE DIRECTIVES..."
                      className="w-full flex-1 min-h-[200px] bg-black border-4 border-white p-4 font-mono text-sm text-neon-pink placeholder:text-zinc-800 focus:outline-none focus:border-neon-pink transition-colors resize-none"
                    />
                    <div className="flex gap-4 self-end">
                      <Button variant="secondary" onClick={() => { setIsEditing(false); void loadProfile(); }}>CANCEL</Button>
                      <Button variant="primary" className="!bg-neon-pink !border-neon-pink hover:!bg-white hover:!text-black" onClick={() => void handleSave()} disabled={isLoading}>
                        {isLoading ? "SAVING..." : "COMMIT_DATA"}
                      </Button>
                    </div>
                  </div>
                ) : (
                  <div className="bg-zinc-950 border-4 border-zinc-800 p-6 flex-1">
                    {about ? (
                      <p className="font-mono text-sm leading-relaxed whitespace-pre-wrap text-white">
                        {about}
                      </p>
                    ) : (
                      <p className="font-mono text-sm text-zinc-700 italic">EMPTY_DATA_BUFFER</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          </Card>
        </motion.div>

        {/* System Settings & Access */}
        <motion.div
           initial={{ opacity: 0, scale: 0.95 }}
           animate={{ opacity: 1, scale: 1 }}
           transition={{ delay: 0.1 }}
           className="flex flex-col gap-8"
        >
          <Card accent="none" label="SYSTEM_ACCESS_LOG">
             <div className="space-y-4">
                <div className="flex justify-between items-center bg-black border-2 border-zinc-800 p-4 font-mono text-sm text-zinc-500">
                  <span>LAST_LOGIN</span>
                  <span className="text-neon-cyan select-none font-bold">JUST_NOW</span>
                </div>
                <div className="flex justify-between items-center bg-black border-2 border-zinc-800 p-4 font-mono text-sm text-zinc-500">
                  <span>ENCRYPTION</span>
                  <span className="text-neon-green select-none font-bold">ACTIVE (RSA-2048)</span>
                </div>
             </div>
          </Card>

          <Card accent="orange" label="DANGER_ZONE">
             <div className="space-y-4 font-mono text-sm">
                <p className="text-zinc-500">INITIATE EXPORT OR ERASURE PROCEDURES FOR RECORDED SYSTEM DATA.</p>
                <div className="flex flex-col gap-4">
                  <Button variant="secondary" fullWidth disabled>
                    EXPORT_JSON_RECORD
                  </Button>
                  <Button variant="danger" fullWidth disabled>
                    INITIATE_DATA_PURGE
                  </Button>
                </div>
             </div>
          </Card>
        </motion.div>

      </section>
    </main>
  );
}
