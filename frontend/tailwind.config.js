/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        // Dark background palette
        dark: {
          950: '#070A0F',
          900: '#0A0D14',
          800: '#0F1420',
          700: '#141B2D',
          600: '#1C2540',
          500: '#243058',
        },
        // Fire orange accent
        fire: {
          50:  '#FFF3EB',
          100: '#FFE0C8',
          200: '#FFC599',
          300: '#FF9F5C',
          400: '#FF7A24',
          500: '#FF5A00',
          600: '#E64D00',
          700: '#CC4400',
          800: '#B33B00',
          900: '#993300',
        },
        // Neutral grays
        slate: {
          850: '#1B2130',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        'fire-gradient': 'linear-gradient(135deg, #FF5A00 0%, #FF9A00 50%, #FFD000 100%)',
        'fire-gradient-subtle': 'linear-gradient(135deg, rgba(255,90,0,0.15) 0%, rgba(255,154,0,0.08) 100%)',
        'dark-gradient': 'linear-gradient(180deg, #070A0F 0%, #0A0D14 100%)',
        'card-gradient': 'linear-gradient(135deg, rgba(255,255,255,0.04) 0%, rgba(255,255,255,0.01) 100%)',
        'glow-orange': 'radial-gradient(ellipse at center, rgba(255,90,0,0.15) 0%, transparent 70%)',
      },
      boxShadow: {
        'fire': '0 0 20px rgba(255, 90, 0, 0.3)',
        'fire-lg': '0 0 40px rgba(255, 90, 0, 0.4)',
        'card': '0 4px 24px rgba(0, 0, 0, 0.5)',
        'card-hover': '0 8px 32px rgba(0, 0, 0, 0.6), 0 0 1px rgba(255,90,0,0.3)',
        'glow': '0 0 15px rgba(255, 90, 0, 0.25)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'float': 'float 6s ease-in-out infinite',
        'shimmer': 'shimmer 2s linear infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}
