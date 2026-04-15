"use client";

import { forwardRef, InputHTMLAttributes, useState } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, hint, className = "", ...props }, ref) => {
    const [isFocused, setIsFocused] = useState(false);

    return (
      <div className="w-full">
        {label && (
          <label className="block font-display text-xs font-semibold uppercase tracking-wider text-text-secondary mb-2">
            {label}
          </label>
        )}
        <input
          ref={ref}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          className={`
            brutal-input
            ${isFocused
              ? "border-neon-violet shadow-[0_0_0_4px_rgba(139,92,246,0.12)]"
              : "border-border-subtle"
            }
            ${error ? "!border-neon-orange !shadow-[0_0_0_4px_rgba(249,115,22,0.12)]" : ""}
            ${className}
          `}
          {...props}
        />
        {hint && !error && (
          <p className="mt-1.5 text-[11px] text-text-muted font-mono">
            {hint}
          </p>
        )}
        {error && (
          <p className="mt-1.5 text-[11px] text-neon-orange font-mono flex items-center gap-1">
            <span>⚠</span> {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
