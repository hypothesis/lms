import {
  buildCSS,
  buildJS,
  generateManifest,
  runTests,
  watchJS,
} from '@hypothesis/frontend-build';
import gulp from 'gulp';

import tailwindConfig from './tailwind.config.js';

gulp.task('build-js', () => buildJS('./rollup.config.js'));
gulp.task('watch-js', () => watchJS('./rollup.config.js'));

gulp.task('build-css', () =>
  buildCSS(
    [
      './lms/static/styles/canvas_pages/canvas_pages.scss',
      './lms/static/styles/moodle_pages/moodle_pages.scss',
      './lms/static/styles/frontend_apps.scss',
      './lms/static/styles/lms.scss',
      './lms/static/styles/ui-playground.scss',
    ],
    { tailwindConfig },
  ),
);

gulp.task('watch-css', () => {
  gulp.watch(
    [
      './lms/static/styles/**/*.{css,scss}',
      './lms/static/scripts/frontend_apps/**/*.js',
      './lms/static/scripts/frontend_apps/**/*.ts',
      './lms/static/scripts/frontend_apps/**/*.tsx',
      './lms/static/scripts/ui-playground/**/*.js',
      './lms/static/scripts/ui-playground/**/*.ts',
      './lms/static/scripts/ui-playground/**/*.tsx',
    ],
    { ignoreInitial: false },
    gulp.series('build-css'),
  );
});

gulp.task('watch-manifest', () => {
  gulp.watch('build/**/*.{css,js,map}', generateManifest);
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
      karmaConfig: 'lms/static/scripts/karma.config.cjs',
      rollupConfig: 'rollup-tests.config.js',
      testsPattern: 'lms/static/scripts/**/*-test.js',
    }),
  ),
);
