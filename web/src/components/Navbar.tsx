"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/context/AuthContext";

const NAV_ITEMS = [
  { href: "/", label: "DASHBOARD", icon: "◈", color: "neon-violet" },
  { href: "/notes", label: "VAULT", icon: "✦", color: "neon-cyan" },
  { href: "/insights", label: "NEURAL", icon: "◉", color: "neon-green" },
  { href: "/profile", label: "USER", icon: "◬", color: "neon-pink" },
] as const;

export default function Navbar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <>
      {/* ── Vertical OS Sidebar ── */}
      <nav className="hidden md:flex fixed left-0 top-0 bottom-0 w-[72px] flex-col items-center py-6 z-50 bg-black border-r-4 border-white">
        {/* OS Logo */}
        <Link href="/" className="mb-10">
          <div className="w-10 h-10 bg-white text-black flex items-center justify-center font-display font-black text-xl shadow-[4px_4px_0_0_#BC13FE]">
            E
          </div>
        </Link>

        {/* Nav Items */}
        <div className="flex-1 flex flex-col items-center gap-6">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link key={item.href} href={item.href} className="flex flex-col items-center group">
                <div
                  className={`
                    w-12 h-12 border-4 flex items-center justify-center text-xl transition-all
                    ${isActive
                      ? "bg-white text-black border-white shadow-[6px_6px_0_0_#BC13FE]"
                      : "bg-black text-zinc-500 border-zinc-800 hover:border-white hover:text-white"
                    }
                  `}
                >
                  {item.icon}
                </div>
                <span className="hidden group-hover:block absolute left-20 bg-white text-black px-2 py-1 font-display font-black text-[8px] tracking-widest whitespace-nowrap shadow-[4px_4px_0_0_#000]">
                  {item.label}
                </span>
              </Link>
            );
          })}
        </div>

        {/* System Power Off */}
        <button
          onClick={() => void logout()}
          className="w-12 h-12 border-4 border-zinc-800 text-zinc-800 hover:border-neon-orange hover:text-neon-orange flex items-center justify-center transition-all bg-black font-black text-sm"
        >
          ⏻
        </button>
      </nav>

      {/* ── Mobile Bottom Bar ── */}
      <nav className="md:hidden fixed bottom-6 left-6 right-6 z-50 flex justify-between bg-black border-4 border-white p-2 shadow-[8px_8px_0_0_#000]">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link key={item.href} href={item.href} className="flex-1">
              <div
                className={`
                  p-3 text-center font-display font-black text-[10px] tracking-tight
                  ${isActive ? "bg-white text-black" : "text-zinc-500"}
                `}
              >
                {item.label}
              </div>
            </Link>
          );
        })}
        <button
          onClick={() => void logout()}
          className="p-3 text-neon-orange font-black text-[10px]"
        >
           QUIT
        </button>
      </nav>
    </>
  );
}
