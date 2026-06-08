/** @type {import("tailwindcss").Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ivory: "#faf9f7",
        stone: "#f3f0eb",
        fog: "#e8e4dc",
        ink: "#2c2c2a",
        mute: "#7a7874",
        amber: "#c4956a",
        "amber-soft": "#dcc4a8",
        border: "#e5e2dc",
        "warn-clay": "#d4a574",
        "block-rose": "#c48b7a",
        "emo-happy": "#a8c97e",
        "emo-sad": "#8fa4c4",
        "emo-angry": "#c48b7a",
        "emo-anxious": "#d4a574",
        "emo-tired": "#b8b0a8",
        "emo-neutral": "#dcc4a8",
      },
      fontFamily: {
        body: ["Source Han Sans CN", "Noto Sans SC", "Inter", "sans-serif"],
        ui: ["Source Han Sans CN", "Noto Sans SC", "Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      borderRadius: {
        bubble: "16px",
        "bubble-sm": "4px",
        panel: "16px",
        input: "16px",
        btn: "12px",
        tag: "8px",
      },
      maxWidth: {
        chat: "65ch",
      },
      spacing: {
        xs: "4px",
        sm: "8px",
        md: "16px",
        lg: "24px",
        xl: "32px",
        "2xl": "48px",
      },
    },
  },
  plugins: [],
};
