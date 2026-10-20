/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          950: '#080C16',
          900: '#0D1527',
          850: '#111C33',
          800: '#172340',
          750: '#1F2E52',
          700: '#2A3C66',
          600: '#3D548C',
        },
        violet: {
          accent: '#8B5CF6',
          glow: '#A78BFA',
          deep: '#4C1D95',
          subtle: 'rgba(139, 92, 246, 0.12)',
        },
        policy: {
          allow: '#10B981',
          approval: '#F59E0B',
          block: '#EF4444',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
}
