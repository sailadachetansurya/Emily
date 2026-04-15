"use client";

import { motion } from "framer-motion";
import { ReactNode, ButtonHTMLAttributes } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: "primary" | "secondary" | "accent" | "danger";
  size?: "sm" | "md" | "lg";
  fullWidth?: boolean;
}

export default function Button({
  children,
  variant = "primary",
  size = "md",
  fullWidth = false,
  className = "",
  disabled,
  ...props
}: ButtonProps) {
  const variantClasses = {
    primary: "bg-white text-black border-white hover:bg-neon-violet hover:border-neon-violet hover:text-white",
    secondary: "bg-transparent text-white border-white hover:bg-white hover:text-black",
    accent: "bg-neon-green text-black border-neon-green hover:bg-white hover:border-white",
    danger: "bg-neon-orange text-black border-neon-orange hover:bg-white hover:border-white",
  };

  const sizeClasses = {
    sm: "px-4 py-2 text-[10px] border-3",
    md: "px-6 py-3 text-xs border-4",
    lg: "px-10 py-5 text-sm border-5",
  };

  return (
    <button
      disabled={disabled}
      className={`
        font-display font-black uppercase tracking-widest
        transition-all duration-75 active:translate-x-1 active:translate-y-1 active:shadow-none
        shadow-[6px_6px_0px_0px_rgba(0,0,0,1)]
        inline-flex items-center justify-center
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${fullWidth ? "w-full" : ""}
        ${disabled ? "opacity-30 cursor-not-allowed shadow-none grayscale" : "cursor-pointer"}
        ${className}
      `}
      style={{ boxShadow: disabled ? 'none' : '6px 6px 0px 0px #000000' }}
      {...props}
    >
      {children}
    </button>
  );
}
