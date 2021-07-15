/* eslint-env node */

const path = require('path');
const glob = require('glob');

const chromeFlags = [];

if (process.env.RUNNING_IN_DOCKER) {
  // Use Chromium from Alpine packages.
  process.env.CHROME_BIN = 'chromium-browser';

  // In Docker, the tests run as root, so the sandbox must be disabled.
  chromeFlags.push('--no-sandbox');
}

module.exports = function (config) {
  let testFiles = ['**/*-test.js'];

  if (config.grep) {
    const allFiles = testFiles
      .map(pattern => glob.sync(pattern, { cwd: __dirname }))
      .flat();
    testFiles = allFiles.filter(path => path.match(config.grep));

    // eslint-disable-next-line no-console
    console.log(`Running tests matching pattern "${config.grep}": `, testFiles);
  }

  config.set({
    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: './',

    // frameworks to use
    // available frameworks: https://npmjs.org/browse/keyword/karma-adapter
    frameworks: ['mocha', 'chai', 'sinon', 'source-map-support'],

    // list of files / patterns to load in the browser
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

    // web server port
    port: 9876,

    // enable / disable colors in the output (reporters and logs)
    colors: true,

    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_INFO,

    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: true,

    // start these browsers
    // available browser launchers: https://npmjs.org/browse/keyword/karma-launcher
    browsers: ['ChromeHeadless_Custom'],

    customLaunchers: {
      ChromeHeadless_Custom: {
        base: 'ChromeHeadless',
        flags: chromeFlags,
      },
    },

    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: false,

    // Log slow tests so we can fix them before they timeout
    reportSlowerThan: 500,
  });
};
