/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Maxwell Design System - "The Study" Theme
        vellum: '#F9F7F1',        // Aged Vellum (main canvas)
        'slate-ui': '#E2E8F0',    // Clean Slate (sidebar/secondary)
        midnight: '#1E293B',       // Midnight Ink (primary text)
        'faded-ink': '#64748B',    // Faded Ink (secondary text)
        bronze: '#B48E55',         // Bronze Accent (primary action)
        'bronze-dark': '#8D6E42',  // Darker bronze for hover
        leatherbound: '#451a03',   // Deep Brown (dark accent)
        redline: '#9F1239',        // Deep Rose (error/editing)
      },
      fontFamily: {
        serif: ['"EB Garamond"', 'Garamond', 'Georgia', 'serif'],
        sans: ['Inter', '"Helvetica Neue"', 'Arial', 'sans-serif'],
      },
      boxShadow: {
        book: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      },
      letterSpacing: {
        'button': '0.05em',
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
  darkMode: 'class',
}
