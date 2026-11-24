/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        darkBg: '#0b1120',
        darkSurface: '#151f32',
        darkCard: '#1e293b',
        primary: {
          DEFAULT: '#38bdf8',
          hover: '#0ea5e9',
          dark: '#0284c7'
        }
      }
    },
  },
  plugins: [],
}

