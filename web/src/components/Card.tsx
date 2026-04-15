"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  variant?: "default" | "accent" | "glow";
  accentColor?: "violet" | "green" | "orange" | "pink" | "cyan";
  onClick?: () => void;
}

export default function Card({
  children,
  className = "",
  variant = "default",
  accentColor = "violet",
  onClick,
}: CardProps) {
  const accentClasses = {
    violet: "border-electric-violet hover:shadow-glow-violet",
    green: "border-electric-green hover:shadow-glow-green",
    orange: "border-electric-orange hover:shadow-glow-orange",
    pink: "border-electric-pink",
    cyan: "border-electric-cyan",
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, ease: "easeOut" }}
      whileHover={{
        x: -4,
        y: -4,
        boxShadow: "8px 8px 0px 0px #000000",
      }}
      whileTap={{
        x: 4,
        y: 4,
        boxShadow: "0px 0px 0px 0px #000000",
      }}
      onClick={onClick}
      className={`
        relative bg-card border-2 border-borderMuted rounded-lg
        shadow-[6px_6px_0px_0px_#000000]
        transition-all duration-150 ease-snap
        ${variant === "accent" ? accentClasses[accentColor] : ""}
        ${onClick ? "cursor-pointer" : ""}
        ${className}
      `}
    >
      {children}
    </motion.div>
  );
}
