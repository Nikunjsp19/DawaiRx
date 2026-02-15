/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: 'var(--color-primary)',
        'primary-dark': 'var(--color-primary-hover)',
        'background-light': '#f6f5f8',
        'background-dark': '#150f23',
        'surface-light': '#ffffff',
        'surface-dark': '#1e1b2e',
      },
    },
  },
  plugins: [],
}
