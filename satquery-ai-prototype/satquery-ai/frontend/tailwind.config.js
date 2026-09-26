/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        ink: { 950: '#080d16', 900: '#0b121f', 800: '#0f1829', 700: '#16223a', 600: '#22304a' },
        mist: { 100: '#e8eef8', 300: '#b4c1d6', 500: '#8494ad', 700: '#55647d' },
        signal: { DEFAULT: '#3dc9b0', dim: '#2a8f7e' },
        amber: { flag: '#f2b544' },
      },
      fontFamily: {
        display: ['Newsreader', 'Georgia', 'serif'],
        sans: ['"IBM Plex Sans"', 'system-ui', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}
