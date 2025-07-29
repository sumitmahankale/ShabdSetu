/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        orange: {
          500: '#f97316',
          600: '#ea580c',
        },
        green: {
          500: '#22c55e',
          600: '#16a34a',
        }
      },
      fontFamily: {
        'hindi': ['Noto Sans Devanagari', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
