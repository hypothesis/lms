'use strict';

/* eslint-env node */
/* eslint-disable no-var, prefer-arrow-callback */

var { mkdirSync } = require('fs');
var path = require('path');

var commander = require('commander');
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
    // Test configuration.
    // See https://github.com/karma-runner/karma-mocha#configuration
    .option('--grep [pattern]', 'Run only tests matching a given pattern')
    .parse(process.argv);

  if (commander.grep) {
    log.info(`Running tests matching pattern /${commander.grep}/`);
  }

  return {
    grep: commander.grep,
  };
}

var taskArgs = parseCommandLine();

var vendorBundles = {
  // jquery: ['jquery'],
};
var vendorModules = ['jquery'];
var vendorNoParseModules = ['jquery'];

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
        noParse: vendorNoParseModules,
      })
    );
  });
  return Promise.all(finished);
});

var bundleBaseConfig = {
  path: SCRIPT_DIR,
  external: vendorModules,
  minify: IS_PRODUCTION_BUILD,
  noParse: vendorNoParseModules,
};

var bundles = [
  {
    name: 'frontend_apps',
    entry: './lms/static/scripts/frontend_apps/index',
  },
  {
    name: 'new_application_instance',
    entry: './lms/static/scripts/new-application-instance.js',
  },
  {
    name: 'postmessage_json_rpc_server',
    entry: './lms/static/scripts/postmessage_json_rpc/server/index',
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
  './lms/static/styles/lms.css',
  './lms/static/styles/reports.css',
  './lms/static/styles/frontend_apps.scss',
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

function runKarma(baseConfig, opts, done) {
  // See https://github.com/karma-runner/karma-mocha#configuration
  var cliOpts = {
    client: {
      mocha: {
        grep: taskArgs.grep,
      },
    },
  };

  var karma = require('karma');
  new karma.Server(
    Object.assign(
      {},
      {
        configFile: path.resolve(__dirname, baseConfig),
      },
      cliOpts,
      opts
    ),
    done
  ).start();
}

gulp.task('test', function(callback) {
  runKarma(
    './lms/static/scripts/karma.config.js',
    { singleRun: true, autoWatch: false },
    callback
  );
});

gulp.task('test-watch', function(callback) {
  runKarma('./lms/static/scripts/karma.config.js', {}, callback);
});

gulp.task('lint', function() {
  // Adapted from usage example at https://www.npmjs.com/package/gulp-eslint
  // `gulp-eslint` is loaded lazily so that it is not required during Docker image builds
  var eslint = require('gulp-eslint');
  return gulp
    .src(['lms/static/scripts/**/*.js'])
    .pipe(eslint())
    .pipe(eslint.format())
    .pipe(eslint.failAfterError());
});
