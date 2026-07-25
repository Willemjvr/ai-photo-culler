/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          900: '#0f0f11',
          800: '#1a1a1e',
          700: '#252529',
          600: '#2f2f35',
        },
        accent: {
          DEFAULT: '#6366f1',
          hover: '#818cf8',
        },
        positive: '#22c55e',
        negative: '#ef4444',
        warning: '#f59e0b',
      },
    },
  },
  plugins: [],
}
