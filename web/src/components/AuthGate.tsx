"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";
import { useAuth } from "@/context/AuthContext";
import { useState } from "react";
import { Input } from "./Input";
import Button from "./Button";

interface AuthGateProps {
  children: ReactNode;
  title?: string;
}

export default function AuthGate({ children, title = "ECHO" }: AuthGateProps) {
  const { user, isLoading, error, login, register, clearError } = useAuth();
  const [usernameInput, setUsernameInput] = useState("");
  const [passwordInput, setPasswordInput] = useState("");
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");

  if (isLoading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-bg-primary">
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex flex-col items-center gap-6"
        >
          <div className="w-16 h-16 rounded-brutal bg-neon-violet flex items-center justify-center font-display font-bold text-2xl text-white shadow-brutal animate-glow-pulse">
            E
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-neon-violet animate-pulse" />
            <span className="font-mono text-xs text-text-secondary tracking-widest uppercase">
              Initializing ECHO
            </span>
          </div>
        </motion.div>
      </main>
    );
  }

  if (!user) {
    const handleSubmit = async () => {
      if (!usernameInput.trim() || !passwordInput.trim()) return;
      clearError();
      setStatusMsg("");
      try {
        if (isRegisterMode) {
          await register(usernameInput, passwordInput);
          setStatusMsg("Account created.");
        } else {
          await login(usernameInput, passwordInput);
          setStatusMsg("Welcome back.");
        }
        setPasswordInput("");
      } catch {
        // error is set by context
      }
    };

    return (
      <main className="min-h-screen flex items-center justify-center bg-bg-primary mesh-gradient p-4">
        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.5, ease: [0.34, 1.56, 0.64, 1] }}
          className="w-full max-w-md"
        >
          <div className="brutal-card p-8 border-neon-violet/30">
            {/* Logo Mark */}
            <div className="flex items-center gap-4 mb-8">
              <div className="w-12 h-12 rounded-brutal-sm bg-neon-violet flex items-center justify-center font-display font-bold text-xl text-white shadow-brutal-sm">
                E
              </div>
              <div>
                <h1 className="text-2xl font-display font-bold tracking-tight">
                  {title}
                </h1>
                <p className="font-mono text-xs text-text-muted tracking-wide">
                  Emotional Chronicle · Helping Observations
                </p>
              </div>
            </div>

            {/* Form */}
            <div className="space-y-4">
              <Input
                label="Username"
                value={usernameInput}
                onChange={(e) => setUsernameInput(e.target.value)}
                placeholder="your handle"
              />
              <Input
                label="Password"
                type="password"
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                placeholder="••••••••"
                onKeyDown={(e) => {
                  if (e.key === "Enter") void handleSubmit();
                }}
              />
            </div>

            <div className="mt-6 flex gap-3">
              <Button
                variant="primary"
                onClick={() => void handleSubmit()}
                className="flex-1"
              >
                {isRegisterMode ? "Create Account" : "Sign In"}
              </Button>
              <Button
                variant="secondary"
                onClick={() => {
                  setIsRegisterMode((v) => !v);
                  clearError();
                  setStatusMsg("");
                }}
              >
                {isRegisterMode ? "Login" : "Register"}
              </Button>
            </div>

            {/* Feedback */}
            {statusMsg && (
              <motion.p
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 font-mono text-xs text-neon-green"
              >
                ✓ {statusMsg}
              </motion.p>
            )}
            {error && (
              <motion.p
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 font-mono text-xs text-neon-orange"
              >
                ⚠ {error}
              </motion.p>
            )}

            {/* Decorative bottom line */}
            <div className="mt-8 flex items-center gap-3">
              <div className="flex-1 h-px bg-gradient-to-r from-neon-violet/40 via-neon-cyan/20 to-transparent" />
              <span className="font-mono text-[10px] text-text-muted uppercase tracking-widest">
                Powered by Emily AI
              </span>
              <div className="flex-1 h-px bg-gradient-to-l from-neon-green/40 via-neon-cyan/20 to-transparent" />
            </div>
          </div>
        </motion.div>
      </main>
    );
  }

  return <>{children}</>;
}
