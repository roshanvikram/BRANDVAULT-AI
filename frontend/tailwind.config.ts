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
        mono: ["var(--font-geist-mono)", "Menlo", "Monaco", "Consolas", "monospace"],
      },
      colors: {
        background: "#F7F7F7",
        foreground: "#0A0A0A",
        mono: {
          50:  "#FFFFFF",
          75:  "#FAFAFA",
          100: "#F7F7F7",
          150: "#F1F1F1",
          200: "#E5E5E5",
          300: "#D4D4D4",
          400: "#A3A3A3",
          500: "#737373",
          600: "#404040",
          800: "#171717",
          950: "#0A0A0A",
        },
        brand: {
          surface:        "#FFFFFF",
          bg:             "#F7F7F7",
          border:         "#E5E5E5",
          borderSubtle:   "rgba(0,0,0,0.06)",
          text:           "#0A0A0A",
          textSub:        "#404040",
          textMuted:      "#737373",
          accent:         "#0A0A0A",
          hover:          "#F5F5F5",
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
        soft:   "0 2px 12px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.04)",
        medium: "0 4px 20px rgba(0,0,0,0.08), 0 2px 6px rgba(0,0,0,0.04)",
        float:  "0 8px 32px rgba(0,0,0,0.10), 0 2px 8px rgba(0,0,0,0.05)",
        card:   "0 1px 4px rgba(0,0,0,0.05), 0 0 1px rgba(0,0,0,0.08)",
      },
      borderRadius: {
        "2xl": "16px",
        "3xl": "20px",
        "4xl": "24px",
      },
      borderColor: {
        DEFAULT: "#E5E5E5",
      },
    },
  },
  plugins: [],
};

export default config;
