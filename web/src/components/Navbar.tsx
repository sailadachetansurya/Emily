"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: "◈", color: "neon-violet" },
  { href: "/notes", label: "Notes", icon: "✦", color: "neon-cyan" },
  { href: "/insights", label: "Insights", icon: "◉", color: "neon-green" },
] as const;

export default function Navbar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);

  if (!user) return null;

  return (
    <>
      {/* ── Desktop Sidebar ── */}
      <nav className="hidden md:flex fixed left-0 top-0 bottom-0 w-[72px] flex-col items-center py-6 z-50 bg-bg-card/80 backdrop-blur-xl border-r border-border-subtle">
        {/* Logo */}
        <Link href="/" className="mb-8 group">
          <div className="w-10 h-10 rounded-brutal-sm bg-neon-violet flex items-center justify-center font-display font-bold text-lg text-white shadow-brutal-sm transition-all group-hover:shadow-brutal group-hover:-translate-x-0.5 group-hover:-translate-y-0.5">
            E
          </div>
        </Link>

        {/* Nav Items */}
        <div className="flex-1 flex flex-col items-center gap-2">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link key={item.href} href={item.href} className="relative group">
                <div
                  className={`
                    w-11 h-11 rounded-brutal-sm flex items-center justify-center text-lg
                    transition-all duration-200 ease-spring
                    ${isActive
                      ? `bg-${item.color} text-black shadow-brutal-sm`
                      : "bg-transparent text-text-secondary hover:text-text-primary hover:bg-bg-elevated"
                    }
                  `}
                >
                  {item.icon}
                </div>
                {/* Tooltip */}
                <div className="absolute left-[calc(100%+12px)] top-1/2 -translate-y-1/2 px-3 py-1.5 bg-bg-elevated border border-border-subtle rounded-brutal-sm font-mono text-xs text-text-primary whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-200 shadow-brutal-sm">
                  {item.label}
                </div>
              </Link>
            );
          })}
        </div>

        {/* User + Logout */}
        <div className="flex flex-col items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-neon-violet/20 border border-neon-violet/30 flex items-center justify-center font-display text-xs text-neon-violet uppercase">
            {user.username[0]}
          </div>
          <button
            onClick={() => void logout()}
            className="w-9 h-9 rounded-brutal-sm flex items-center justify-center text-text-muted hover:text-neon-orange hover:bg-neon-orange/10 transition-all text-sm"
            title="Logout"
          >
            ⏻
          </button>
        </div>
      </nav>

      {/* ── Mobile Bottom Bar ── */}
      <nav className="md:hidden fixed bottom-4 left-1/2 -translate-x-1/2 z-50">
        <div className="flex items-center gap-1 bg-bg-card/90 backdrop-blur-xl border-2 border-border-subtle rounded-2xl shadow-brutal-sm px-2 py-2">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link key={item.href} href={item.href}>
                <div
                  className={`
                    px-4 py-2.5 rounded-xl font-mono text-xs font-semibold
                    transition-all duration-200 ease-spring
                    ${isActive
                      ? `bg-${item.color} text-black shadow-brutal-sm`
                      : "text-text-secondary hover:text-text-primary"
                    }
                  `}
                >
                  <span className="mr-1">{item.icon}</span>
                  {item.label}
                </div>
              </Link>
            );
          })}
          <button
            onClick={() => void logout()}
            className="px-3 py-2.5 rounded-xl font-mono text-xs text-text-muted hover:text-neon-orange transition-all"
          >
            ⏻
          </button>
        </div>
      </nav>
    </>
  );
}
