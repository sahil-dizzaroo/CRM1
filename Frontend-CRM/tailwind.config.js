/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // Dizzaroo Brand Colors
      colors: {
        'dizzaroo': {
          'deep-blue': '#1E73BE',
          'deep-blue-light': '#4A9FE8',
          'deep-blue-dark': '#155A94',
          'soft-green': '#76C893',
          'soft-green-light': '#A4D9B5',
          'soft-green-dark': '#5BA374',
          'blue-green': '#168AAD',
          'blue-green-light': '#4BA8C5',
          'blue-green-dark': '#116B87',
        },
        // Flat color names for easier access
        'dizzaroo-deep-blue': '#1E73BE',
        'dizzaroo-soft-green': '#76C893',
        'dizzaroo-blue-green': '#168AAD',
        // Legacy support
        primary: {
          DEFAULT: '#1E73BE',
          50: '#E6F2FF',
          100: '#CCE5FF',
          200: '#99CBFF',
          300: '#66B1FF',
          400: '#3397FF',
          500: '#1E73BE',
          600: '#155A94',
          700: '#0D416A',
          800: '#052840',
          900: '#020F16',
        },
        secondary: {
          DEFAULT: '#76C893',
          50: '#F0F9F4',
          100: '#E1F3E9',
          200: '#C3E7D3',
          300: '#A4D9B5',
          400: '#86CD97',
          500: '#76C893',
          600: '#5BA374',
          700: '#457A58',
          800: '#2E513C',
          900: '#172820',
        },
      },
      // Dizzaroo DNA Gradient
      backgroundImage: {
        'dizzaroo-gradient': 'linear-gradient(135deg, #168AAD, #76C893)',
        'dizzaroo-gradient-hover': 'linear-gradient(135deg, #1E73BE, #76C893)',
        'dizzaroo-dna-gradient': 'linear-gradient(135deg, #168AAD, #76C893)',
      },
      // Urbanist Font Family
      fontFamily: {
        sans: ['Urbanist', 'system-ui', '-apple-system', 'sans-serif'],
        primary: ['Urbanist', 'sans-serif'],
      },
      // Typography Scale (with adjusted line-heights)
      fontSize: {
        'title': ['60px', { lineHeight: '1.2', letterSpacing: '-0.015em' }],      // text-6xl
        'heading': ['42px', { lineHeight: '1.25', letterSpacing: '-0.015em' }],   // text-4xl
        'subheading': ['36px', { lineHeight: '1.3', letterSpacing: '-0.015em' }], // text-3xl
        'medium-body': ['28px', { lineHeight: '1.35', letterSpacing: '0em' }],     // text-2xl
        'body': ['20px', { lineHeight: '1.4', letterSpacing: '0em' }],           // text-xl
      },
      // Border Radius (rounded UI)
      borderRadius: {
        'dizzaroo-sm': '0.5rem',
        'dizzaroo-md': '0.75rem',
        'dizzaroo-lg': '1rem',
        'dizzaroo-xl': '1.25rem',
      },
      // Custom Shadows
      boxShadow: {
        'dizzaroo': '0 4px 14px 0 rgba(30, 115, 190, 0.15)',
        'dizzaroo-lg': '0 10px 25px -5px rgba(30, 115, 190, 0.2)',
      },
    },
  },
  plugins: [],
}

