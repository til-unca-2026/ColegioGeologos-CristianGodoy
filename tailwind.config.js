/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
    './static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          500: '#15803d',
          600: '#166534',
          700: '#1b4332',
          800: '#143d32',
          900: '#0d2821',
          dark: '#12372A',
        },
      },
    },
  },
  plugins: [],
};
