// frontend/vue_frontend/tailwind.config.js
/** @type {import('tailwindcss').Config} */
import colors from 'tailwindcss/colors' // <-- Import default colors

export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Change primary to Indigo
        'primary': colors.indigo[600],         // #4f46e5
        'primary-hover': colors.indigo[700],    // #4338ca
        // Keep others or customize further
        'secondary': colors.gray[600],          // #4b5563
        'light': colors.gray[100],            // #f3f4f6
        'dark': colors.gray[800],             // #1f2937
        // You can add more custom colors here
      },
      fontFamily: {
         sans: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
}