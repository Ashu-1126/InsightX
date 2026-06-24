import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: "#0a0a0f",
        surface: "#111118",
        surface2: "#1a1a2e",
        border: "#2a2a3e",
        text: "#e2e8f0",
        primary: "#00d4ff",
        secondary: "#7c3aed",
        warning: "#f59e0b",
        danger: "#ef4444",
        success: "#10b981",
        muted: "#94a3b8",
      },
      fontFamily: {
        mono: ["IBM Plex Mono", "monospace"],
        sans: ["Space Grotesk", "sans-serif"],
      },
      animation: {
        pulse_slow: "pulse 3s cubic-bezier(0.4,0,0.6,1) infinite",
        "spin-slow": "spin 8s linear infinite",
        glow: "glow 2s ease-in-out infinite alternate",
      },
      keyframes: {
        glow: {
          "0%": { boxShadow: "0 0 5px #00d4ff40" },
          "100%": { boxShadow: "0 0 20px #00d4ff80, 0 0 40px #00d4ff30" },
        },
      },
      backgroundImage: {
        "grid-pattern":
          "linear-gradient(rgba(0,212,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0,212,255,0.03) 1px, transparent 1px)",
      },
      backgroundSize: {
        "grid-sm": "40px 40px",
      },
    },
  },
  plugins: [],
};

export default config;
