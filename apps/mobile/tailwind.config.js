/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        background: '#0b0f19',
        card: '#111827',
        emerald: {
          500: '#10b981'
        },
        cyan: {
          500: '#06b6d4'
        }
      }
    },
  },
  plugins: [],
}
