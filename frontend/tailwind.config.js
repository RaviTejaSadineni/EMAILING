/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        navy: '#0a0e27',
        electric: '#667eea',
        purple: '#764ba2',
      },
      boxShadow: {
        glass: '0 8px 32px rgba(102, 126, 234, 0.2)',
        glow: '0 0 30px rgba(102, 126, 234, 0.35)',
        card3d: '0 20px 30px rgba(10, 14, 39, 0.45)',
      },
    },
  },
  plugins: [],
}
