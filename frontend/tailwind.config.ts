import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-geist-sans)", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        mono: ["var(--font-geist-sans)", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
        code: ["var(--font-geist-mono)", "Menlo", "Monaco", "Consolas", "monospace"],
      },
      colors: {
        background: "#F8FAFC",
        foreground: "#0F172A",
        brand: {
          50:  "#EEF2FF",
          100: "#E0E7FF",
          200: "#C7D2FE",
          300: "#A5B4FC",
          400: "#818CF8",
          500: "#6366F1",
          600: "#4F46E5",
          700: "#4338CA",
          800: "#3730A3",
          900: "#312E81",
          950: "#1E1B4B",
          surface:      "#FFFFFF",
          bg:           "#F8FAFC",
          border:       "#E2E8F0",
          borderSubtle: "rgba(226,232,240,0.8)",
          text:         "#0F172A",
          textSub:      "#475569",
          textMuted:    "#64748B",
          accent:       "#4F46E5",
          hover:        "#F1F5F9",
        },
      },
      backdropBlur: {
        xs:  "4px",
        sm:  "8px",
        md:  "12px",
        lg:  "18px",
        xl:  "24px",
        "2xl": "32px",
      },
      boxShadow: {
        soft:    "0 1px 3px rgba(15,23,42,0.04), 0 6px 16px -4px rgba(79,70,229,0.04)",
        medium:  "0 4px 12px -2px rgba(15,23,42,0.06), 0 2px 6px -1px rgba(79,70,229,0.04)",
        float:   "0 12px 32px -8px rgba(15,23,42,0.12), 0 4px 12px -2px rgba(79,70,229,0.08)",
        card:    "0 1px 3px rgba(15,23,42,0.05), 0 1px 2px rgba(15,23,42,0.03)",
        primary: "0 4px 14px 0 rgba(79,70,229,0.25)",
      },
      borderRadius: {
        "2xl": "16px",
        "3xl": "20px",
        "4xl": "24px",
      },
      borderColor: {
        DEFAULT: "#E2E8F0",
      },
    },
  },
  plugins: [],
};

export default config;
