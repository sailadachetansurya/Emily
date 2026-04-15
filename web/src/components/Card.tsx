"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

interface CardProps {
  children: ReactNode;
  className?: string;
  accent?: "violet" | "green" | "orange" | "pink" | "cyan" | "none";
  label?: string; // OS-style window label
  onClick?: () => void;
}

export default function Card({
  children,
  className = "",
  accent = "none",
  label,
  onClick,
}: CardProps) {
  const accentClasses = {
    violet: "card-violet",
    green: "card-green",
    orange: "card-orange",
    pink: "border-[#FF007F]",
    cyan: "border-[#00F3FF]",
    none: "border-white",
  };

  const headerBg = {
    violet: "bg-neon-violet",
    green: "bg-neon-green",
    orange: "bg-neon-orange",
    pink: "bg-neon-pink",
    cyan: "bg-neon-cyan",
    none: "bg-white",
  };

  return (
    <div
      onClick={onClick}
      className={`
        brutal-card ${accentClasses[accent]}
        flex flex-col
        ${onClick ? "cursor-pointer" : ""}
        ${className}
      `}
    >
      {/* OS Window Header */}
      {label && (
        <div className={`h-8 border-b-4 border-inherit ${headerBg[accent]} flex items-center px-4 justify-between`}>
          <span className="font-display text-[10px] font-black text-black tracking-widest uppercase">
            {label}
          </span>
          <div className="flex gap-1">
            <div className="w-3 h-3 border-2 border-black" />
            <div className="w-3 h-3 border-2 border-black bg-black" />
          </div>
        </div>
      )}
      
      <div className="p-6 flex-1">
        {children}
      </div>
      
      {/* Decorative OS Corner */}
      <div className="absolute bottom-1 right-1 w-3 h-3 bg-white" style={{ clipPath: 'polygon(100% 0, 100% 100%, 0 100%)' }} />
    </div>
  );
}
