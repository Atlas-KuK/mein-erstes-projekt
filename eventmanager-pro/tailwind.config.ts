import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Eigenes Farbschema: Anthrazit-Basis, warme Gastro-Akzente
        base: {
          50:  '#f5f6f8',
          100: '#e6e8ec',
          200: '#c9ced6',
          300: '#a1a9b6',
          400: '#717b8b',
          500: '#505b6c',
          600: '#3b4555',
          700: '#2a3240',
          800: '#1d2330',
          900: '#141925',
          950: '#0c101a',
        },
        accent: {
          // kupfer/messing – passt zu Gastronomie
          DEFAULT: '#c9934a',
          hover:   '#d9a55b',
          muted:   '#8a6632',
        },
        status: {
          bestaetigt:   '#10b981', // grün
          offen:        '#f59e0b', // gelb
          bearbeitung:  '#3b82f6', // blau
          abgelehnt:    '#ef4444', // rot
          storniert:    '#6b7280', // grau
          abgeschlossen:'#8b5cf6', // lila
        },
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
    },
  },
  plugins: [],
};

export default config;
