module.exports = {
  content: [
    './templates/main/**/*.html',
    './static/main/js/**/*.js'
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        display: ['"Inter Display"', 'sans-serif'],
      },
      fontSize: {
        mlg: '0.925rem',  // Equal to standard "text-md" size
        base: '0.875rem',  // Equal to standard "text-sm" size
        sm: '0.8125rem',  // Halfway between standard "text-xs" and standard "text-sm"
        xxs: '0.6875rem',  // Extra extra small
      }
    }
  },
  plugins: [],
  darkMode: 'class',
  variants: {
    extend: {
      opacity: ['group-hover'],
    },
  },
}