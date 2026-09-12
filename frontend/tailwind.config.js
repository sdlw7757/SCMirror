/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  theme: {
    extend: {
      colors: {
        // 深蓝青科技风
        ink: {
          950: '#05080f',
          900: '#0a0f1c',
          850: '#0d1424',
          800: '#101a2e',
          700: '#16223c',
        },
        cyan: {
          300: '#67e8f9',
          400: '#22d3ee',
          500: '#06b6d4',
          600: '#0891b2',
        },
        glow: {
          cyan: '0 0 34px rgba(34, 211, 238, 0.16), 0 8px 40px rgba(6, 182, 212, 0.12)',
        },
      },
      fontFamily: {
        sans: [
          'Inter',
          'PingFang SC',
          'Microsoft YaHei',
          'Noto Sans SC',
          'system-ui',
          '-apple-system',
          'Segoe UI',
          'sans-serif',
        ],
        mono: ['JetBrains Mono', 'SFMono-Regular', 'Consolas', 'Menlo', 'monospace'],
      },
      boxShadow: {
        card: '0 10px 30px -12px rgba(0,0,0,0.6), 0 0 0 1px rgba(148,163,184,0.08)',
        cardhover:
          '0 22px 48px -18px rgba(0,0,0,0.75), 0 0 44px rgba(34,211,238,0.18)',
        'glow-cyan': '0 8px 40px rgba(34, 211, 238, 0.22), 0 2px 12px rgba(6, 182, 212, 0.18)',
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        floaty: 'floaty 6s ease-in-out infinite',
        pulseSlow: 'pulseSlow 5s ease-in-out infinite',
      },
      keyframes: {
        floaty: {
          '0%,100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-12px)' },
        },
        pulseSlow: {
          '0%,100%': { opacity: '0.5' },
          '50%': { opacity: '0.9' },
        },
      },
    },
  },
  plugins: [],
}
