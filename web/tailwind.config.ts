import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/context/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#050508",
          surface: "#0a0a0f",
          card: "#111118",
          elevated: "#18181f",
        },
        neon: {
          violet: "#8B5CF6",
          green: "#A3E635",
          orange: "#F97316",
          pink: "#EC4899",
          cyan: "#06B6D4",
          yellow: "#FACC15",
        },
        text: {
          primary: "#F4F4F5",
          secondary: "#A1A1AA",
          muted: "#52525B",
        },
        border: {
          hard: "#FFFFFF",
          subtle: "#27272A",
        },
        // Keep backward compat for existing classes
        background: "#050508",
        surface: "#0a0a0f",
        card: "#111118",
        electric: {
          violet: "#8B5CF6",
          green: "#A3E635",
          orange: "#F97316",
          pink: "#EC4899",
          cyan: "#06B6D4",
        },
        borderMuted: "#27272A",
        textMuted: "#A1A1AA",
      },
      fontFamily: {
        display: ["Space Grotesk", "system-ui", "sans-serif"],
        body: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      fontSize: {
        "hero": ["4rem", { lineHeight: "1.05", fontWeight: "700", letterSpacing: "-0.03em" }],
        "title": ["2rem", { lineHeight: "1.15", fontWeight: "700", letterSpacing: "-0.02em" }],
        "subtitle": ["1.25rem", { lineHeight: "1.4", fontWeight: "500" }],
      },
      borderRadius: {
        "brutal": "16px",
        "brutal-sm": "12px",
        "brutal-lg": "20px",
      },
      boxShadow: {
        "brutal-sm": "4px 4px 0px 0px #000000",
        "brutal": "6px 6px 0px 0px #000000",
        "brutal-lg": "8px 8px 0px 0px #000000",
        "brutal-active": "0px 0px 0px 0px #000000",
        "glow-violet": "0 0 20px rgba(139, 92, 246, 0.4), 0 0 60px rgba(139, 92, 246, 0.1)",
        "glow-green": "0 0 20px rgba(163, 230, 53, 0.4), 0 0 60px rgba(163, 230, 53, 0.1)",
        "glow-orange": "0 0 20px rgba(249, 115, 22, 0.4), 0 0 60px rgba(249, 115, 22, 0.1)",
        "glow-cyan": "0 0 20px rgba(6, 182, 212, 0.4), 0 0 60px rgba(6, 182, 212, 0.1)",
        "inner-glow": "inset 0 1px 0 0 rgba(255,255,255,0.05)",
      },
      animation: {
        "glow-pulse": "glowPulse 3s ease-in-out infinite alternate",
        "float": "floatSmooth 6s ease-in-out infinite",
        "slide-up": "slideUp 400ms cubic-bezier(0.34, 1.56, 0.64, 1)",
        "fade-in": "fadeIn 300ms ease-out",
      },
      keyframes: {
        glowPulse: {
          "0%": { boxShadow: "0 0 8px rgba(139, 92, 246, 0.3)" },
          "100%": { boxShadow: "0 0 24px rgba(139, 92, 246, 0.6)" },
        },
        floatSmooth: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-8px)" },
        },
        slideUp: {
          from: { opacity: "0", transform: "translateY(16px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        fadeIn: {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
      },
      transitionTimingFunction: {
        "spring": "cubic-bezier(0.34, 1.56, 0.64, 1)",
      },
    },
  },
  plugins: [],
};

export default config;
