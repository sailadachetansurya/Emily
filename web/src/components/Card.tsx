"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  accent?: "violet" | "green" | "orange" | "pink" | "cyan" | "none";
  glow?: boolean;
  onClick?: () => void;
  // Backward compat
  variant?: string;
  accentColor?: string;
}

const accentBorderMap = {
  violet: "border-neon-violet/40",
  green: "border-neon-green/40",
  orange: "border-neon-orange/40",
  pink: "border-neon-pink/40",
  cyan: "border-neon-cyan/40",
  none: "border-border-subtle",
} as const;

const glowMap = {
  violet: "hover:shadow-glow-violet",
  green: "hover:shadow-glow-green",
  orange: "hover:shadow-glow-orange",
  pink: "hover:shadow-glow-violet",
  cyan: "hover:shadow-glow-cyan",
  none: "",
} as const;

export default function Card({
  children,
  className = "",
  accent = "none",
  glow = false,
  onClick,
  variant,
  accentColor,
}: CardProps) {
  // Support old API
  const resolvedAccent = (accentColor as CardProps["accent"]) || accent;

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.34, 1.56, 0.64, 1] }}
      whileHover={{
        x: -3,
        y: -3,
        boxShadow: "8px 8px 0px 0px #000000",
        transition: { duration: 0.2 },
      }}
      whileTap={{
        x: 3,
        y: 3,
        boxShadow: "0px 0px 0px 0px #000000",
        transition: { duration: 0.1 },
      }}
      onClick={onClick}
      className={`
        relative bg-bg-card/80 backdrop-blur-sm 
        border-2 ${accentBorderMap[resolvedAccent]} 
        rounded-brutal shadow-brutal-sm
        transition-colors duration-200
        ${glow ? glowMap[resolvedAccent] : ""}
        ${onClick ? "cursor-pointer" : ""}
        ${className}
      `}
    >
      {/* Top accent line */}
      {resolvedAccent !== "none" && (
        <div
          className={`absolute top-0 left-4 right-4 h-[2px] rounded-full opacity-60`}
          style={{
            background: `var(--neon-${resolvedAccent})`,
          }}
        />
      )}
      {children}
    </motion.div>
  );
}
