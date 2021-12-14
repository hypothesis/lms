import tailwindConfig from '@hypothesis/frontend-shared/lib/tailwind.preset.js';

export default {
  presets: [tailwindConfig],
  content: [
    './lms/static/scripts/frontend_apps/**/*.js',
    './lms/static/scripts/ui-playground/**/*.js',
  ],
  theme: {
  },
  corePlugins: {
    preflight: false, // Disable Tailwind's CSS reset in the `base` layer
  },
};
