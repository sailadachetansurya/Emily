import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      // NEUBRUTALISM + OLED DARK THEME
      colors: {
        // Base
        background: "#050505",
        surface: "#0a0a0a",
        card: "#121212",

        // Neon Accents - "The Neon Remedy"
        electric: {
          violet: "#8B5CF6",  // Empathy
          green: "#A3E635",   // Recovery (Acid Green)
          orange: "#F97316",  // Triggers (Blaze Orange)
          pink: "#EC4899",    // Highlights
          cyan: "#06B6D4",    // Info
        },

        // Borders & Strokes
        border: "#FFFFFF",
        borderMuted: "#333333",

        // Text
        text: "#FFFFFF",
        textMuted: "#A1A1AA",
      },
      fontFamily: {
        display: ["Orbitron", "Archivo Black", "sans-serif"],
        body: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      fontSize: {
        "xs": ["0.75rem", { lineHeight: "1rem", fontWeight: "400" }],
        "sm": ["0.875rem", { lineHeight: "1.25rem", fontWeight: "400" }],
        "base": ["1rem", { lineHeight: "1.5rem", fontWeight: "400" }],
        "lg": ["1.125rem", { lineHeight: "1.75rem", fontWeight: "500" }],
        "xl": ["1.25rem", { lineHeight: "1.75rem", fontWeight: "600" }],
        "2xl": ["1.5rem", { lineHeight: "2rem", fontWeight: "700" }],
        "3xl": ["2rem", { lineHeight: "2.5rem", fontWeight: "800" }],
        "4xl": ["2.5rem", { lineHeight: "3rem", fontWeight: "900" }],
        "5xl": ["3.5rem", { lineHeight: "1", fontWeight: "900" }],
      },
      borderWidth: {
        "3": "3px",
        "4": "4px",
        "hard": "2px",
      },
      boxShadow: {
        // HARD SHADOWS - NO SOFT BLUR
        "hard-sm": "4px 4px 0px 0px #000000",
        "hard": "6px 6px 0px 0px #000000",
        "hard-lg": "8px 8px 0px 0px #000000",
        "hard-xl": "10px 10px 0px 0px #000000",

        // Neon glow variants
        "glow-violet": "0 0 20px rgba(139, 92, 246, 0.5)",
        "glow-green": "0 0 20px rgba(163, 230, 53, 0.5)",
        "glow-orange": "0 0 20px rgba(249, 115, 22, 0.5)",
      },
      borderRadius: {
        "none": "0",
        "sm": "4px",
        "md": "8px",
        "lg": "12px",
        "xl": "16px",
        "2xl": "24px",
        "full": "9999px",
      },
      animation: {
        "pulse-fast": "pulse 1s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "bounce-short": "bounce 0.3s ease-in-out 3",
        "glow": "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        glow: {
          "0%": { boxShadow: "0 0 5px rgba(139, 92, 246, 0.3)" },
          "100%": { boxShadow: "0 0 20px rgba(139, 92, 246, 0.8)" },
        },
      },
      transitionTimingFunction: {
        "spring": "cubic-bezier(0.34, 1.56, 0.64, 1)",
        "snap": "cubic-bezier(0.5, 0, 1, 1)",
      },
      transitionDuration: {
        "150": "150ms",
        "200": "200ms",
      },
    },
  },
  plugins: [],
};

export default config;
