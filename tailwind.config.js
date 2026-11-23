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
        // ====================================================================
        // SECCIÓN ETIQUETAS Y ESTADOS (Badges / Semáforos / Estados del Sistema)
        // Comprende tanto las etiquetas informativas y semáforos como estados
        // ====================================================================
        badge: {
          // 1. Estados / Etiquetas Semáforo
          'semaforo-green-bg': '#dcfce7',      // Fondo verde suave
          'semaforo-green-text': '#166534',    // Texto verde oscuro
          'semaforo-green-dot': '#16a34a',     // Punto verde
          'semaforo-green-border': '#bbf7d0',  // Borde verde suave

          'semaforo-yellow-bg': '#fef3c7',     // Fondo amarillo suave
          'semaforo-yellow-text': '#92400e',   // Texto ámbar oscuro
          'semaforo-yellow-dot': '#f59e0b',    // Punto ámbar
          'semaforo-yellow-border': '#fde68a', // Borde ámbar suave

          'semaforo-red-bg': '#ffe4e6',        // Fondo rojo suave
          'semaforo-red-text': '#9f1239',      // Texto rojo oscuro
          'semaforo-red-dot': '#f43f5e',       // Punto rojo
          'semaforo-red-border': '#fecdd3',    // Borde rojo suave

          // 2. Etiquetas Informativas / Estándar (Documentos, Contenidos, Títulos, Comisiones, etc.)
          'info-bg': '#eff6ff',                // Azul suave
          'info-text': '#1e40af',              // Azul oscuro
          'info-border': '#bfdbfe',            // Borde azul sutil
        },

        // ====================================================================
        // COLORES INSTITUCIONALES (3 Pilares del Diseño)
        // Modificar aquí en el futuro para cambiar la identidad del sitio completo
        // ====================================================================
        primary: {
          light: '#dcfce7',   // Fondo suave institucional
          DEFAULT: '#15803d', // COLOR 1: Primario institucional (Verde base)
          hover: '#166534',   // Interacción / Hover
          dark: '#143d32',    // Header, menús oscuros, acento profundo
          footer: '#0f2d24',  // Footer institucional
          // Escala de compatibilidad para evitar rupturas visuales en componentes heredados
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#143d32',
        },

        secondary: {
          light: '#f1f5f9',   // Fondo neutro / slate suave
          DEFAULT: '#475569', // COLOR 2: Secundario institucional (Gris pizarra / neutro elegante)
          hover: '#334155',   // Hover secundario
          border: '#cbd5e1',  // Bordes de botones secundarios
        },

        tertiary: {
          light: '#fef3c7',   // Fondo suave acento
          DEFAULT: '#d97706', // COLOR 3: Terciario institucional (Ámbar / Geología / Acento)
          hover: '#b45309',   // Hover terciario
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
