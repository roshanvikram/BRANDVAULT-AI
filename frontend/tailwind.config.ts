import type { Config } from "tailwindcss";

// Professional palette: azure blue accent, navy secondary, cool silver greys.
// (Names kept from the previous theme so existing classes keep working.)
const SIGNAL = {  // azure blue accent
  50: "#EFF5FF", 100: "#DBE8FE", 200: "#BFD5FD", 300: "#93B8FB", 400: "#6093F6",
  500: "#3B6FEF", 600: "#2554D9", 700: "#1D42B8", 800: "#1E3894", 900: "#1E3375", 950: "#152147",
};
// Navy for gradients that used violet/purple.
const DEEP_RED = {
  50: "#F0F4FA", 100: "#DDE6F2", 200: "#BCCBE3", 300: "#8FA6CC", 400: "#5F7BAD",
  500: "#3F5B8F", 600: "#2E4675", 700: "#24385E", 800: "#1C2C4B", 900: "#16233C", 950: "#0D1626",
};
// Moonlit-silver greys that end in charcoal.
const CHARCOAL = {
  50: "#F6F7F9", 100: "#ECEEF1", 200: "#DCE0E5", 300: "#C3C8CF", 400: "#9AA1AA",
  500: "#727881", 600: "#555A62", 700: "#3E4248", 800: "#2E3135", 900: "#222427", 950: "#151618",
};

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
      // Theme: azure blue accent, navy, silver greys ending in charcoal.
      // indigo resolves to azure, violet/purple/pink to navy, slate to the greys.
      // Red (rose/red classes) is kept only for errors and critical findings.
      colors: {
        background: "#E6E9ED",
        foreground: "#222427",
        white: "#FCFCFD",
        silver: { DEFAULT: "#E6E9ED", 50: "#FCFCFD", 100: "#F2F4F6", 200: "#E6E9ED", 300: "#D5DAE0" },
        signal: SIGNAL,
        indigo: SIGNAL,
        brand: { ...SIGNAL, surface: "#FCFCFD", bg: "#E6E9ED", border: "#DCE0E5", borderSubtle: "rgba(220,224,229,0.8)",
                 text: "#222427", textSub: "#4A4F56", textMuted: "#727881", accent: "#2554D9", hover: "#E4E7EB" },
        violet: DEEP_RED,
        purple: DEEP_RED,
        pink: DEEP_RED,
        fuchsia: SIGNAL,
        slate: CHARCOAL,
        charcoal: { DEFAULT: "#222427", 900: "#222427", 950: "#151618", glow: "#3B6FEF" },
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
        soft:    "0 1px 3px rgba(34,36,39,0.04), 0 6px 16px -4px rgba(37,84,217,0.04)",
        medium:  "0 4px 12px -2px rgba(34,36,39,0.06), 0 2px 6px -1px rgba(37,84,217,0.04)",
        float:   "0 12px 32px -8px rgba(34,36,39,0.12), 0 4px 12px -2px rgba(37,84,217,0.08)",
        card:    "0 1px 3px rgba(34,36,39,0.05), 0 1px 2px rgba(34,36,39,0.03)",
        primary: "0 4px 14px 0 rgba(37,84,217,0.25)",
      },
      borderRadius: {
        "2xl": "16px",
        "3xl": "20px",
        "4xl": "24px",
      },
      borderColor: {
        DEFAULT: "#DCE0E5",
      },
    },
  },
  plugins: [],
};

export default config;
