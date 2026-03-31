/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg:           '#111111',
        surface:      '#1e1e1e',
        raised:       '#272727',
        border:       '#333333',
        text:         '#f0f0f0',
        muted:        '#888888',
        subtle:       '#555555',
        accent:       '#4caf8a',
        'accent-hover': '#5dc99f',
        'accent-dim': '#1e3d30',
        danger:       '#e05555',
        warn:         '#d4a017',
        'warn-dim':   '#3a2e0a',
      },
    },
  },
  plugins: [],
}
