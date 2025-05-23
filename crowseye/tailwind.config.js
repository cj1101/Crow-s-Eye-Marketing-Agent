/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx}',
    './components/**/*.{js,ts,jsx,tsx}',
    './features/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        'crow-purple': {
          DEFAULT: '#6d28d9',
          light: '#8b5cf6',
          dark: '#5b21b6',
        },
      },
    },
  },
  plugins: [],
}; 