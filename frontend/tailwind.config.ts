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
        background: "#FFFFFF",
        foreground: "#0A0A0A",
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
          surface: "#FFFFFF",
          card: "#FFFFFF",
          border: "#E5E5E5",
          borderSubtle: "#F0F0F0",
          textPrimary: "#0A0A0A",
          textSecondary: "#404040",
          textMuted: "#737373",
          accent: "#0A0A0A",
          hover: "#F5F5F5",
        }
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["GeistMono", "Menlo", "Monaco", "Consolas", "monospace"],
      },
      borderColor: {
        DEFAULT: "#E5E5E5",
      }
    },
  },
  plugins: [],
};
export default config;
