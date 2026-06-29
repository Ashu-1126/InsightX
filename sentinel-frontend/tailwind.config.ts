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
        // CAESAR palette: Black #000000 · Burgundy #6D001A · White #FFFFFF
        bg: "#000000",
        surface: "#0d0608",
        surface2: "#1a0a0f",
        border: "#3a1620",
        text: "#ffffff",
        primary: "#6D001A",
        secondary: "#a8324a",
        warning: "#f59e0b",
        danger: "#ef4444",
        success: "#10b981",
        muted: "#b8a0a6",
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
          "0%": { boxShadow: "0 0 5px #6D001A40" },
          "100%": { boxShadow: "0 0 20px #6D001A99, 0 0 40px #6D001A40" },
        },
      },
      backgroundImage: {
        "grid-pattern":
          "linear-gradient(rgba(109,0,26,0.06) 1px, transparent 1px), linear-gradient(90deg, rgba(109,0,26,0.06) 1px, transparent 1px)",
      },
      backgroundSize: {
        "grid-sm": "40px 40px",
      },
    },
  },
  plugins: [],
};

export default config;
