import tailwindConfig from '@hypothesis/frontend-shared/lib/tailwind.preset.js';

const successGreen =
  tailwindConfig.theme?.extend?.colors?.green?.success ?? '#00a36d';

export default /** @type {Partial<import('tailwindcss').Config>} */ ({
  presets: [tailwindConfig],
  content: [
    './lms/static/scripts/frontend_apps/**/*.{js,ts,tsx}',
    './lms/static/scripts/ui-playground/**/*.{js,ts,tsx}',
    // This script adds a DOM element with the `.browser-check-warning` class
    './lms/static/scripts/browser_check/index.ts',
    './node_modules/@hypothesis/frontend-shared/lib/**/*.js',
  ],
  theme: {
    extend: {
      animation: {
        gradeSubmitSuccess: 'gradeSubmitSuccess 2s ease-out forwards',
      },
      colors: {
        grade: {
          success: '#005c3d',
          'success-light': '#dfebe7',
          error: '#891b1d',
          'error-light': '#f0e2e3',
          warning: '#774903',
          'warning-light': '#fef7ec',
        },
      },
      fontFamily: {
        sans: [
          '"Helvetica Neue"',
          'Helvetica',
          'Arial',
          '"Lucida Grande"',
          'sans-serif',
        ],
      },
      fontSize: {
        tiny: ['13px', { lineHeight: '15px' }], // Legacy body font size for LMS
      },
      keyframes: {
        gradeSubmitSuccess: {
          from: { backgroundColor: successGreen },
          to: { backgroundColor: 'transparent' },
        },
      },
    },
  },
});
