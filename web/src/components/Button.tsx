"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";
import type { HTMLMotionProps } from "framer-motion";

interface ButtonProps extends Omit<HTMLMotionProps<"button">, "children"> {
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
  ...props
}: ButtonProps) {
  const variantClasses = {
    primary: "bg-electric-violet text-white border-white hover:bg-electric-violet/90",
    secondary: "bg-transparent text-white border-white hover:bg-white hover:text-black",
    accent: "bg-electric-green text-black border-white hover:bg-electric-green/90",
    danger: "bg-electric-orange text-black border-white hover:bg-electric-orange/90",
  };

  const sizeClasses = {
    sm: "px-4 py-2 text-xs",
    md: "px-6 py-3 text-sm",
    lg: "px-8 py-4 text-base",
  };

  return (
    <motion.button
      whileHover={{
        x: -2,
        y: -2,
        boxShadow: "6px 6px 0px 0px #000000",
      }}
      whileTap={{
        x: 2,
        y: 2,
        boxShadow: "0px 0px 0px 0px #000000",
      }}
      className={`
        font-display font-bold uppercase tracking-wider
        border-2 rounded-md
        shadow-[4px_4px_0px_0px_#000000]
        transition-all duration-150 ease-snap
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${fullWidth ? "w-full" : ""}
        ${className}
      `}
      {...props}
    >
      {children}
    </motion.button>
  );
}
