'use strict';

/* eslint-env node */

const { mkdirSync, writeFileSync } = require('fs');
const path = require('path');

const commander = require('commander');
const glob = require('glob');
const gulp = require('gulp');
const log = require('gulplog');
const rollup = require('rollup');
const through = require('through2');

const createStyleBundle = require('./scripts/gulp/create-style-bundle');
const manifest = require('./scripts/gulp/manifest');

const IS_PRODUCTION_BUILD = process.env.NODE_ENV === 'production';

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

/** @param {import('rollup').RollupWarning} */
function logRollupWarning(warning) {
  log.info(`Rollup warning: ${warning} (${warning.url})`);
}

async function buildJS(rollupConfig) {
  let { default: configs } = await import(rollupConfig);
  if (!Array.isArray(configs)) {
    configs = [configs];
  }

  await Promise.all(
    configs.map(async config => {
      const bundle = await rollup.rollup({
        ...config,
        onwarn: logRollupWarning,
      });
      await bundle.write(config.output);
    })
  );
}

async function watchJS(rollupConfig) {
  const { default: configs } = await import(rollupConfig);
  const watcher = rollup.watch(
    configs.map(config => ({
      ...config,
      onwarn: logRollupWarning,
    }))
  );

  return new Promise(resolve => {
    watcher.on('event', event => {
      switch (event.code) {
        case 'START':
          log.info('JS build starting...');
          break;
        case 'BUNDLE_END':
          event.result.close();
          break;
        case 'ERROR':
          log.info('JS build error', event.error);
          break;
        case 'END':
          log.info('JS build completed.');
          resolve(); // Resolve once the initial build completes.
          break;
      }
    });
  });
}

gulp.task('build-js', () => buildJS('./rollup.config.mjs'));
gulp.task('watch-js', () => watchJS('./rollup.config.mjs'));

const cssBundles = [
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

const MANIFEST_SOURCE_FILES = [
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
      through.obj(function (file, enc, callback) {
        log.info('Updated asset manifest');
        this.push(file);
        callback();
      })
    )
    .pipe(gulp.dest('build/'));
}

gulp.task('watch-manifest', () => {
  gulp.watch(MANIFEST_SOURCE_FILES, generateManifest);
});

gulp.task('build', gulp.series(['build-js', 'build-css'], generateManifest));

gulp.task('watch', gulp.parallel(['watch-js', 'watch-css', 'watch-manifest']));

async function buildAndRunTests() {
  const { grep, singleRun } = karmaOptions;

  // Generate an entry file for the test bundle. This imports all the test
  // modules, filtered by the pattern specified by the `--grep` CLI option.
  const testFiles = [
    'lms/static/scripts/bootstrap.js',
    ...glob
      .sync('lms/static/scripts/**/*-test.js')
      .filter(path => (grep ? path.match(grep) : true)),
  ];

  const testSource = testFiles
    .map(path => `import "../../${path}";`)
    .join('\n');

  mkdirSync('build/scripts', { recursive: true });
  writeFileSync('build/scripts/test-inputs.js', testSource);

  // Build the test bundle.
  log.info(`Building test bundle... (${testFiles.length} files)`);
  if (singleRun) {
    await buildJS('./rollup-tests.config.mjs');
  } else {
    await watchJS('./rollup-tests.config.mjs');
  }

  // Run the tests.
  log.info('Starting Karma...');
  return new Promise(resolve => {
    const karma = require('karma');
    new karma.Server(
      karma.config.parseConfig(
        path.resolve(__dirname, './lms/static/scripts/karma.config.js'),
        { singleRun }
      ),
      resolve
    ).start();

    process.on('SIGINT', () => {
      // Give Karma a chance to handle SIGINT and cleanup, but forcibly
      // exit if it takes too long.
      setTimeout(() => {
        resolve();
        process.exit(1);
      }, 5000);
    });
  });
}

// Unit and integration testing tasks.
//
// Some (eg. a11y) tests rely on CSS bundles. We assume that JS will always take
// longer to build than CSS, so build in parallel.
gulp.task('test', gulp.parallel('build-css', buildAndRunTests));
