"use client";

import { forwardRef, InputHTMLAttributes, useState } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = "", ...props }, ref) => {
    const [isFocused, setIsFocused] = useState(false);

    return (
      <div className="w-full">
        {label && (
          <label className="block font-display text-xs uppercase tracking-wider text-textMuted mb-2">
            {label}
          </label>
        )}
        <input
          ref={ref}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          className={`
            w-full px-4 py-3
            bg-surface border-2 rounded-md
            font-mono text-sm
            text-text placeholder:text-textMuted
            transition-all duration-150 ease-snap
            focus:outline-none
            ${isFocused
              ? "border-electric-violet shadow-[0_0_15px_rgba(139,92,246,0.3)]"
              : "border-borderMuted"
            }
            ${error ? "border-electric-orange" : ""}
            ${className}
          `}
          {...props}
        />
        {error && (
          <p className="mt-1 text-xs text-electric-orange font-mono">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
