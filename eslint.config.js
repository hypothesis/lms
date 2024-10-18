import hypothesisBase from 'eslint-config-hypothesis/base';
import hypothesisJSX from 'eslint-config-hypothesis/jsx';
import hypothesisTS from 'eslint-config-hypothesis/ts';
import globals from 'globals';

export default [
  {
    ignores: [
      '.tox/**/*',
      '.yalc/**/*',
      '.yarn/**/*',
      'build/**/*',
      '**/coverage/**/*',
      'docs/_build/*',
    ],
  },

  ...hypothesisBase,
  ...hypothesisJSX,
  ...hypothesisTS,

  // Additional rules that require type information. These can only be run
  // on files included in the TS project by tsconfig.json.
  {
    files: ['lms/static/scripts/frontend_apps/**/*.{js,ts,tsx}'],
    ignores: ['**/test/*.js'],
    rules: {
      '@typescript-eslint/no-unnecessary-condition': 'error',
    },
    languageOptions: {
      parserOptions: {
        project: 'lms/static/scripts/tsconfig.json',
      },
    },
  },

  // Code that runs in Node
  {
    files: ['*'],
    ignores: ['lms/**'],
    languageOptions: {
      globals: {
        ...globals.node,
      },
    },
  },
];
