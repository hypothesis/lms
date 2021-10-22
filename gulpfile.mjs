import {
  buildCSS,
  buildJS,
  runTests,
  watchJS,
} from '@hypothesis/frontend-build';

import gulp from 'gulp';
import log from 'gulplog';
import through from 'through2';

// TODO - Move this to the @hypothesis/frontend-build package
import manifest from './scripts/gulp/manifest.js';

gulp.task('build-js', () => buildJS('./rollup.config.mjs'));
gulp.task('watch-js', () => watchJS('./rollup.config.mjs'));

gulp.task('build-css', () =>
  buildCSS([
    './lms/static/styles/lms.scss',
    './lms/static/styles/reports.css',
    './lms/static/styles/frontend_apps.scss',
    './lms/static/styles/ui-playground/ui-playground.scss',
  ])
);

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

// Unit and integration testing tasks.
//
// Some (eg. a11y) tests rely on CSS bundles. We assume that JS will always take
// longer to build than CSS, so build in parallel.
gulp.task(
  'test',
  gulp.parallel('build-css', () =>
    runTests({
      bootstrapFile: 'lms/static/scripts/bootstrap.js',
      karmaConfig: 'lms/static/scripts/karma.config.js',
      rollupConfig: 'rollup-tests.config.mjs',
      testsPattern: 'lms/static/scripts/**/*-test.js',
    })
  )
);
