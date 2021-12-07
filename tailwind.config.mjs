import tailwindConfig from '@hypothesis/frontend-shared/lib/tailwind.preset.js';

export default {
  presets: [tailwindConfig],
  content: [
    './lms/static/scripts/frontend_apps/**/*.js',
    './lms/static/scripts/ui-playground/**/*.js',
  ],
  theme: {
    extend: {
      animation: {
        gradeSubmitSuccess: 'gradeSubmitSuccess 2s ease-out forwards',
        validationMessageOpen: 'validationMessageOpen 0.3s forwards',
        validationMessageClose: 'validationMessageClose 0.3s forwards',
      },
      keyframes: {
        gradeSubmitSuccess: {
          from: { backgroundColor: tailwindConfig.theme.colors.success },
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
  corePlugins: {
    preflight: false, // Disable Tailwind's CSS reset in the `base` layer
  },
};
