/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0d0f1a",
        foreground: "#e8eaf0",
        panel: "#111422",
        panelBorder: "#1e2235",
        accent: "#6366f1",
        accentHover: "#4f52d4",
        mutedText: "#8892aa",
        heading: "#ffffff",
      },
      fontFamily: {
        sans: ["DM Sans", "sans-serif"],
        mono: ["DM Mono", "monospace"],
      },
    },
  },
  plugins: [],
}
