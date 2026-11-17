/** @type {import('tailwindcss').Config} */
module.exports = {
  // Habilita el modo oscuro controlado por clase CSS (p. ej. <html class="dark">)
  darkMode: 'class',

  content: [
    './templates/**/*.html',
    './apps/**/templates/**/*.html',
    './static/js/**/*.js',
  ],

  theme: {
    extend: {
      // 1. PALETA DE COLORES SEMÁNTICA
      colors: {
        // Color Primario (identidad institucional: verde actual, fácilmente cambiable)
        primary: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#143d32',   // Header / menús
          dark: '#12372A',  // Tono institucional profundo
          footer: '#0f2d24',// Footer actual
          DEFAULT: '#15803d',
        },

        // Color Secundario / Acento (para llamadas a la acción, insignias, geología/tierra)
        accent: {
          light: '#fef3c7',
          DEFAULT: '#d97706',
          hover: '#b45309',
          dark: '#78350f',
        },

        // Superficies y Fondos preparados para Modo Claro y Modo Oscuro
        surface: {
          ground: '#f8fafc',       // Fondo general (slate-50)
          card: '#ffffff',         // Tarjetas / paneles en modo claro
          darkground: '#0b1320',   // Fondo general en modo oscuro
          darkcard: '#152238',     // Tarjetas en modo oscuro
          border: '#e2e8f0',       // Bordes en modo claro
          darkborder: '#1e293b',   // Bordes en modo oscuro
        },

        // Estados del sistema (mensajes, alertas, validaciones)
        state: {
          success: '#15803d',
          'success-bg': '#f0fdf4',
          'success-border': '#bbf7d0',

          error: '#b91c1c',
          'error-bg': '#fef2f2',
          'error-border': '#fecaca',

          warning: '#b45309',
          'warning-bg': '#fffbeb',
          'warning-border': '#fde68a',

          info: '#1d4ed8',
          'info-bg': '#eff6ff',
          'info-border': '#bfdbfe',
        },

        // Mantenemos compatibilidad con 'brand' por si alguna plantilla lo referencia
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

      // 2. TIPOGRAFÍAS
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
        heading: ['Inter', 'system-ui', 'sans-serif'],
      },

      // 3. BORDES REDONDEADOS ESTÁNDAR
      borderRadius: {
        btn: '0.5rem',       // rounded-lg para botones
        card: '0.75rem',     // rounded-xl para tarjetas
        badge: '9999px',     // rounded-full para insignias/pills
      },

      // 4. SOMBRAS INSTITUCIONALES
      boxShadow: {
        soft: '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
        card: '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05)',
      },
    },
  },
  plugins: [],
};

