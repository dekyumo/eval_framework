/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        "background": "#0c0e13",
        "surface": "#0c0e13",
        "surface-dim": "#0c0e13",
        "surface-bright": "#282c37",
        "surface-container-lowest": "#000000",
        "surface-container-low": "#11131a",
        "surface-container": "#161921",
        "surface-container-high": "#1c2028",
        "surface-container-highest": "#212630",
        "surface-variant": "#212630",
        "on-surface": "#e2e5f3",
        "on-surface-variant": "#a7abb8",
        "outline": "#717582",
        "outline-variant": "#444853",
        "primary": "#cabeff",
        "primary-fixed": "#7c5cff",
        "primary-container": "#542bd6",
        "on-primary": "#4100c5",
        "on-primary-container": "#e7dfff",
        "secondary": "#bec7d8",
        "secondary-container": "#333c4a",
        "tertiary": "#ff85a2",
        "error": "#f97386",
        "error-container": "#871c34",
        "on-error-container": "#ff97a3",
        
        // Semantic
        "semantic-pass": "#31C48D",
        "semantic-fail": "#F5698E",
        "semantic-margin": "#F6A609",
        "semantic-ood": "#7A8393",
        "semantic-info": "#7C5CFF",
        "blame-caller": "#F6A609",
        "blame-agent": "#F5698E",
        "blame-framework": "#C24BFF"
      },
      fontFamily: {
        "headline": ["Space Grotesk", "sans-serif"],
        "body": ["Inter", "sans-serif"],
        "mono": ["JetBrains Mono", "monospace"]
      },
      borderRadius: {
        "sm": "0.25rem",
        "DEFAULT": "0.5rem",
        "md": "0.75rem",
        "lg": "1rem",
        "full": "9999px"
      }
    },
  },
  plugins: [],
}
