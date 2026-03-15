import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        term: {
          black: "#000000",
          bg: "#050510",
          panel: "#080810",
          surface: "#0c0c1a",
          border: "#1a1a35",
          "border-bright": "#252545",
          orange: "#FF6A00",
          "orange-dim": "#CC5500",
          "orange-glow": "#FF4500",
          green: "#00CC00",
          "green-bright": "#33FF33",
          red: "#FF2020",
          "red-dim": "#CC1919",
          yellow: "#FFD600",
          blue: "#1565C0",
          "blue-bright": "#2196F3",
          "blue-deep": "#0D47A1",
          cyan: "#00BCD4",
          white: "#EAEAEA",
          text: "#C8C8D0",
          muted: "#707088",
          dim: "#454560",
          "muted-dark": "#2a2a45",
        },
      },
      fontFamily: {
        terminal: [
          "Consolas",
          "SF Mono",
          "Fira Code",
          "Cascadia Code",
          "Monaco",
          "Courier New",
          "monospace",
        ],
      },
      fontSize: {
        xxs: ["10px", { lineHeight: "14px" }],
        xs: ["11px", { lineHeight: "16px" }],
        sm: ["12px", { lineHeight: "18px" }],
        base: ["13px", { lineHeight: "20px" }],
        lg: ["14px", { lineHeight: "20px" }],
        xl: ["16px", { lineHeight: "22px" }],
        "2xl": ["18px", { lineHeight: "24px" }],
        "3xl": ["22px", { lineHeight: "28px" }],
        "4xl": ["28px", { lineHeight: "34px" }],
        "5xl": ["36px", { lineHeight: "42px" }],
      },
    },
  },
  plugins: [],
};

export default config;
