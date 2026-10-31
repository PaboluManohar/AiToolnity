import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#171916",
        paper: "#f7f7f3",
        accent: "#355f48",
        "accent-soft": "#e6eee8",
      },
    },
  },
  plugins: [],
};

export default config;
