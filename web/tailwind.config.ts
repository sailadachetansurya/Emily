import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#050505", // OLED Pitch Black
          surface: "#0A0A0A",
          card: "#0F0F0F",
        },
        neon: {
          violet: "#BC13FE", // Electric Violet (Empathy)
          green: "#BFFF00", // Acid Green (Recovery)
          orange: "#FF6700", // Blaze Orange (Triggers)
          pink: "#FF007F",
          cyan: "#00F3FF",
        },
        border: {
          brutal: "#FFFFFF",
          muted: "#1A1A1A",
        },
      },
      fontFamily: {
        display: ["Orbitron", "Archivo Black", "sans-serif"],
        heavy: ["Archivo Black", "sans-serif"],
        mono: ["'JetBrains Mono'", "monospace"],
        digital: ["'Courier New'", "monospace"], // Digital Readout fallback
      },
      boxShadow: {
        "hard": "8px 8px 0px 0px #000000",
        "hard-sm": "4px 4px 0px 0px #000000",
        "hard-lg": "12px 12px 0px 0px #000000",
        "hard-neon-violet": "8px 8px 0px 0px #BC13FE",
        "hard-neon-green": "8px 8px 0px 0px #BFFF00",
        "hard-neon-orange": "8px 8px 0px 0px #FF6700",
      },
      borderRadius: {
        "none": "0",
        "sm": "2px",
        "md": "4px",
      },
      borderWidth: {
        "3": "3px",
        "4": "4px",
        "5": "5px",
      },
    },
  },
  plugins: [],
};

export default config;
