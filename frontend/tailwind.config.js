/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: 'hsl(217, 91%, 60%)',
          foreground: 'hsl(0, 0%, 100%)',
          glow: 'hsl(217, 100%, 70%)',
          dark: 'hsl(217, 91%, 45%)',
        },
        secondary: {
          DEFAULT: 'hsl(217, 19%, 27%)',
          foreground: 'hsl(0, 0%, 100%)',
          light: 'hsl(217, 32%, 17%)',
        },
        accent: {
          DEFAULT: 'hsl(260, 84%, 57%)',
          foreground: 'hsl(0, 0%, 100%)',
        },
        success: {
          DEFAULT: 'hsl(142, 76%, 36%)',
          foreground: 'hsl(0, 0%, 100%)',
        },
        warning: {
          DEFAULT: 'hsl(38, 92%, 50%)',
          foreground: 'hsl(0, 0%, 100%)',
        },
        error: {
          DEFAULT: 'hsl(0, 84%, 60%)',
          foreground: 'hsl(0, 0%, 100%)',
        },
        destructive: {
          DEFAULT: 'hsl(0, 84%, 60%)',
          foreground: 'hsl(0, 0%, 100%)',
        },
        muted: {
          DEFAULT: 'hsl(210, 40%, 96.1%)',
          foreground: 'hsl(215.4, 16.3%, 46.9%)',
        },
        border: 'hsl(214.3, 31.8%, 91.4%)',
        input: 'hsl(214.3, 31.8%, 91.4%)',
        ring: 'hsl(222.2, 84%, 4.9%)',
        background: 'hsl(240, 12%, 98%)',
        foreground: 'hsl(224, 16%, 12%)',
        card: {
          DEFAULT: 'hsl(0, 0%, 100%)',
          foreground: 'hsl(222.2, 84%, 4.9%)',
        },
        popover: {
          DEFAULT: 'hsl(0, 0%, 100%)',
          foreground: 'hsl(222.2, 84%, 4.9%)',
        },
        sidebar: {
          DEFAULT: 'hsl(0, 0%, 98%)',
          foreground: 'hsl(240, 5.3%, 26.1%)',
          primary: 'hsl(240, 5.9%, 10%)',
          'primary-foreground': 'hsl(0, 0%, 98%)',
          accent: 'hsl(240, 4.8%, 95.9%)',
          'accent-foreground': 'hsl(240, 5.9%, 10%)',
          border: 'hsl(214.3, 31.8%, 91.4%)',
          ring: 'hsl(222.2, 84%, 4.9%)',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        'soft': '0 2px 15px -3px rgba(0, 0, 0, 0.07), 0 10px 20px -2px rgba(0, 0, 0, 0.04)',
        'medium': '0 4px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        'strong': '0 10px 40px -10px rgba(0, 0, 0, 0.15), 0 4px 25px -5px rgba(0, 0, 0, 0.1)',
      },
      borderRadius: {
        'xl': '0.75rem',
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, hsl(217, 91%, 60%), hsl(217, 100%, 70%))',
        'gradient-secondary': 'linear-gradient(135deg, hsl(217, 19%, 27%), hsl(217, 32%, 17%))',
        'gradient-hero': 'linear-gradient(135deg, hsl(217, 91%, 60%), hsl(260, 84%, 57%))',
      },
      boxShadow: {
        'soft': '0 1px 2px 0 hsl(217, 91%, 60% / 0.05)',
        'medium': '0 4px 6px -1px hsl(217, 91%, 60% / 0.1)',
        'large': '0 10px 15px -3px hsl(217, 91%, 60% / 0.1)',
        'glow': '0 0 20px hsl(217, 91%, 60% / 0.4), 0 0 40px hsl(217, 100%, 70% / 0.2)',
      }
    },
  },
  plugins: [],
}