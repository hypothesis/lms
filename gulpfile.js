'use strict';

/* eslint-env node */
/* eslint-disable no-var, prefer-arrow-callback */

var { mkdirSync } = require('fs');
var path = require('path');

const commander = require('commander');
var gulp = require('gulp');
var log = require('gulplog');
var through = require('through2');

var createBundle = require('./scripts/gulp/create-bundle');
var createStyleBundle = require('./scripts/gulp/create-style-bundle');
var manifest = require('./scripts/gulp/manifest');

var IS_PRODUCTION_BUILD = process.env.NODE_ENV === 'production';
var SCRIPT_DIR = 'build/scripts';

function parseCommandLine() {
  commander
    .option(
      '--grep <pattern>',
      'Run only tests where filename matches a regex pattern'
    )
    .option('--watch', 'Continuously run tests (default: false)', false)
    .option('--browser <browser>', 'Run tests in browser of choice.')
    .option(
      '--no-browser',
      "Don't launch default browser. Instead, navigate to http://localhost:9876/ to run the tests."
    )
    .parse(process.argv);

  const { grep, watch, browser } = commander.opts();
  const karmaOptions = {
    grep: grep,
    singleRun: !watch,
  };

  // browser option can be either false | undefined | string
  if (browser === false) {
    karmaOptions.browsers = null;
  } else if (browser) {
    karmaOptions.browsers = [browser];
  }

  return karmaOptions;
}

const karmaOptions = parseCommandLine();

// We do not currently generate any vendor JS bundles, but the infrastructure
// is left here in case we decide to add them in future.
var vendorBundles = {
  // bundleName: ['<import-name>'],
};
var vendorModules = [];

// Builds the bundles containing vendor JS code
gulp.task('build-vendor-js', function() {
  var finished = [];
  Object.keys(vendorBundles).forEach(function(name) {
    finished.push(
      createBundle({
        name: name,
        require: vendorBundles[name],
        minify: IS_PRODUCTION_BUILD,
        path: SCRIPT_DIR,
        noParse: [],
      })
    );
  });
  return Promise.all(finished);
});

var bundleBaseConfig = {
  path: SCRIPT_DIR,
  external: vendorModules,
  minify: IS_PRODUCTION_BUILD,
  noParse: [],
};

var bundles = [
  {
    name: 'frontend_apps',
    entry: './lms/static/scripts/frontend_apps/index.js',
  },
  {
    name: 'new_application_instance',
    entry: './lms/static/scripts/new-application-instance.js',
  },
  {
    name: 'browser_check',
    entry: './lms/static/scripts/browser_check/index.js',
  },
  {
    name: 'ui-playground',
    entry: './lms/static/scripts/ui-playground/index.js',
  },
];

var bundleConfigs = bundles.map(function(config) {
  return Object.assign({}, bundleBaseConfig, config);
});

gulp.task(
  'build-js',
  gulp.series(['build-vendor-js'], function() {
    return Promise.all(
      bundleConfigs.map(function(config) {
        return createBundle(config);
      })
    );
  })
);

gulp.task(
  'watch-js',
  gulp.series(['build-vendor-js'], function() {
    bundleConfigs.forEach(function(config) {
      createBundle(config, { watch: true });
    });
  })
);

var cssBundles = [
  './lms/static/styles/lms.scss',
  './lms/static/styles/reports.css',
  './lms/static/styles/frontend_apps.scss',
  './lms/static/styles/ui-playground/ui-playground.scss',
];

gulp.task('build-css', () => {
  mkdirSync('build/styles', { recursive: true });
  const bundles = cssBundles.map(entry =>
    createStyleBundle({
      input: entry,
      output: `build/styles/${path.basename(entry, path.extname(entry))}.css`,
      minify: IS_PRODUCTION_BUILD,
    })
  );
  return Promise.all(bundles);
});

gulp.task('watch-css', () => {
  gulp.watch(
    './lms/static/styles/**/*.{css,scss}',
    { ignoreInitial: false },
    gulp.series('build-css')
  );
});

var MANIFEST_SOURCE_FILES = [
  'build/**/*.css',
  'build/**/*.js',
  'build/**/*.map',
];

/**
 * Generate a JSON manifest mapping file paths to
 * URLs containing cache-busting query string parameters.
 */
function generateManifest() {
  return gulp
    .src(MANIFEST_SOURCE_FILES)
    .pipe(manifest({ name: 'manifest.json' }))
    .pipe(
      through.obj(function(file, enc, callback) {
        log.info('Updated asset manifest');
        this.push(file);
        callback();
      })
    )
    .pipe(gulp.dest('build/'));
}

gulp.task('watch-manifest', function() {
  gulp.watch(MANIFEST_SOURCE_FILES, generateManifest);
});

gulp.task('build', gulp.series(['build-js', 'build-css'], generateManifest));

gulp.task('watch', gulp.parallel(['watch-js', 'watch-css', 'watch-manifest']));

function runKarma(done) {
  const karma = require('karma');
  new karma.Server(
    karma.config.parseConfig(
      path.resolve(__dirname, './lms/static/scripts/karma.config.js'),
      karmaOptions
    ),
    done
  ).start();

  process.on('SIGINT', () => {
    // Give Karma a chance to handle SIGINT and cleanup, but forcibly
    // exit if it takes too long.
    setTimeout(() => {
      done();
      process.exit(1);
    }, 5000);
  });
}

// Unit and integration testing tasks.
// Some (eg. a11y) tests rely on CSS bundles, so build these first.
gulp.task(
  'test',
  gulp.series('build-css', done => runKarma(done))
);
