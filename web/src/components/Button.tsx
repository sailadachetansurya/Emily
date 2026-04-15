"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";
import type { HTMLMotionProps } from "framer-motion";

interface ButtonProps extends Omit<HTMLMotionProps<"button">, "children"> {
  children: ReactNode;
  variant?: "primary" | "secondary" | "accent" | "danger" | "ghost";
  size?: "sm" | "md" | "lg";
  fullWidth?: boolean;
  icon?: ReactNode;
}

export default function Button({
  children,
  variant = "primary",
  size = "md",
  fullWidth = false,
  icon,
  className = "",
  disabled,
  ...props
}: ButtonProps) {
  const variantClasses = {
    primary: "bg-neon-violet text-white border-neon-violet/60 hover:bg-neon-violet/90",
    secondary: "bg-bg-elevated text-text-primary border-border-subtle hover:bg-border-hard hover:text-bg-primary hover:border-border-hard",
    accent: "bg-neon-green text-black border-neon-green hover:bg-neon-green/90",
    danger: "bg-neon-orange text-black border-neon-orange hover:bg-neon-orange/90",
    ghost: "bg-transparent text-text-secondary border-transparent hover:text-text-primary hover:bg-bg-elevated shadow-none hover:shadow-none",
  };

  const sizeClasses = {
    sm: "px-3 py-1.5 text-[11px] rounded-lg",
    md: "px-5 py-2.5 text-[13px] rounded-brutal-sm",
    lg: "px-8 py-3.5 text-sm rounded-brutal",
  };

  return (
    <motion.button
      whileHover={disabled ? {} : {
        x: -2,
        y: -2,
        boxShadow: "6px 6px 0px 0px #000000",
        transition: { duration: 0.15 },
      }}
      whileTap={disabled ? {} : {
        x: 2,
        y: 2,
        boxShadow: "0px 0px 0px 0px #000000",
        transition: { duration: 0.08 },
      }}
      disabled={disabled}
      className={`
        inline-flex items-center justify-center gap-2
        font-display font-semibold uppercase tracking-wider
        border-2 shadow-brutal-sm
        transition-colors duration-150
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${fullWidth ? "w-full" : ""}
        ${disabled ? "opacity-40 cursor-not-allowed !shadow-none" : "cursor-pointer"}
        ${className}
      `}
      {...props}
    >
      {icon && <span className="text-sm">{icon}</span>}
      {children}
    </motion.button>
  );
}
