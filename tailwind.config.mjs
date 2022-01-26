import tailwindConfig from '@hypothesis/frontend-shared/lib/tailwind.preset.js';

const successGreen =
  tailwindConfig.theme?.extend?.colors?.green?.success ?? '#00a36d';

export default {
  presets: [tailwindConfig],
  content: [
    './lms/static/scripts/frontend_apps/**/*.js',
    './lms/static/scripts/ui-playground/**/*.js',
    './node_modules/@hypothesis/frontend-shared/lib/**/*.js',
  ],
  theme: {
    extend: {
      animation: {
        gradeSubmitSuccess: 'gradeSubmitSuccess 2s ease-out forwards',
        validationMessageOpen: 'validationMessageOpen 0.3s forwards',
        validationMessageClose: 'validationMessageClose 0.3s forwards',
      },
      colors: {
        green: {
          success: successGreen,
        },
        yellow: {
          notice: '#fbc168',
        },
        red: {
          error: '#d93c3f',
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
        validationMessageOpen: {
          from: { opacity: 0, width: 0 },
          to: { opacity: 0.9, width: '300px' },
        },
        validationMessageClose: {
          from: { opacity: 0.9, width: '300px' },
          to: { opacity: 0, width: 0 },
        },
      },
      spacing: {
        'touch-minimum': '44px', // Equivalent to spacing 11; minimum touch-target size
      },
    },
  },
};
