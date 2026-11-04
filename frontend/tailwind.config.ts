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
        background: "#0A0A0A",
        foreground: "#F5F5F5",
        mono: {
          50: "#FFFFFF",
          100: "#F5F5F5",
          200: "#E5E5E5",
          400: "#A3A3A3",
          500: "#737373",
          600: "#404040",
          900: "#171717",
          950: "#0A0A0A",
        },
        brand: {
          surface: "#171717",
          card: "#121212",
          border: "#404040",
          borderSubtle: "#262626",
          textPrimary: "#F5F5F5",
          textSecondary: "#A3A3A3",
          textMuted: "#737373",
          accent: "#FFFFFF",
          hover: "#262626",
        }
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["GeistMono", "Menlo", "Monaco", "Consolas", "monospace"],
      },
      borderColor: {
        DEFAULT: "#404040",
      }
    },
  },
  plugins: [],
};
export default config;
