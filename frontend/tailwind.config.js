/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Background levels
        'page':    '#1A1B2E',
        'panel':   '#232436',
        'hover':   '#2C2D42',
        'input':   '#191A2C',
        'sidebar': '#16172A',

        // Brand
        'brand':   '#FACC15',

        // Semantic
        'success': '#22C55E',
        'failure': '#EF4444',
        'warning': '#F59E0B',
        'info':    '#3B82F6',
        'timeout': '#A855F7',

        // Text
        'text-primary':   '#E5E7EB',
        'text-secondary': '#9CA3AF',
        'text-muted':     '#6B7280',
        'text-disabled':  '#4B5563',

        // Borders
        'border-main': '#374151',
        'border-dim':  '#2D2E40',
      },
      fontFamily: {
        sans: ['Inter', 'SF Pro Text', '-apple-system', 'Segoe UI', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
