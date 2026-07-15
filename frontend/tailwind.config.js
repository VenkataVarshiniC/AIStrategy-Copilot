/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#0B1D33",
          light: "#132A47",
          lighter: "#1C3A5E",
        },
        paper: "#F7F5F0",
        gold: {
          DEFAULT: "#B08D57",
          light: "#CBA96E",
          dark: "#8C6E3E",
        },
        slate: {
          DEFAULT: "#4A5568",
        },
        signal: {
          support: "#2F6F4F",
          refute: "#B5533C",
          partial: "#B08D57",
          pending: "#6B7280",
        },
      },
      fontFamily: {
        display: ["\"Source Serif 4\"", "Georgia", "serif"],
        sans: ["\"Inter\"", "system-ui", "sans-serif"],
        mono: ["\"IBM Plex Mono\"", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgba(11,29,51,0.06), 0 4px 16px rgba(11,29,51,0.06)",
      },
    },
  },
  plugins: [],
};
