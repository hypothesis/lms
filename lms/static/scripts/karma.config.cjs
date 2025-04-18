/* global __dirname require module */

// eslint-disable-next-line @typescript-eslint/no-require-imports
const path = require('path');

module.exports = function (config) {
  config.set({
    // Base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: './',

    frameworks: ['mocha', 'chai', 'sinon', 'source-map-support'],

    files: [
      // Test bundles.
      { pattern: '../../../build/scripts/tests.bundle.js', type: 'module' },

      // Sourcemaps for test bundles.
      { pattern: '../../../build/scripts/*.js.map', included: false },

      // CSS bundles.
      // Accessibility tests rely on having styles available.
      '../../../build/styles/*.css',
    ],

    coverageIstanbulReporter: {
      dir: path.join(__dirname, '../../../coverage'),
      reports: ['json', 'html'],
      'report-config': {
        json: { subdir: './' },
      },
      thresholds: {
        global: {
          statements: 100,
        },
      },
    },

    mochaReporter: {
      // Display a helpful diff when comparing complex objects
      // See https://www.npmjs.com/package/karma-mocha-reporter#showdiff
      showDiff: true,
      // Only show the total test counts and details for failed tests
      output: 'minimal',
    },

    // Use https://www.npmjs.com/package/karma-mocha-reporter
    // for more helpful rendering of test failures
    reporters: ['mocha', 'coverage-istanbul'],

    browsers: ['ChromeHeadless'],

    // Log slow tests so we can fix them before they timeout
    reportSlowerThan: 500,
  });
};
