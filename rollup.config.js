import fs from 'node:fs';
import path from 'node:path';

import { babel } from '@rollup/plugin-babel';
import commonjs from '@rollup/plugin-commonjs';
import { nodeResolve } from '@rollup/plugin-node-resolve';
import replace from '@rollup/plugin-replace';
import terser from '@rollup/plugin-terser';
import virtual from '@rollup/plugin-virtual';

const FRONTEND_SHARED = 'node_modules/@hypothesis/frontend-shared';
const FRONTEND_SHARED_DEEP_IMPORT = '@hypothesis/frontend-shared/lib/';

/**
 * Resolve `@hypothesis/frontend-shared/lib/...` imports to the files on disk.
 *
 * The UI playground reaches into the package for `pattern-library` and its
 * `Library` component, but the package's `exports` map only publishes
 * `.` and `./pattern-library`. Node (and so `@rollup/plugin-node-resolve`)
 * refuses the deeper paths, and Rollup then leaves them as bare imports the
 * browser cannot load, breaking the playground bundle at runtime.
 *
 * Only the playground uses these paths, so the app bundles are unaffected.
 */
function resolveFrontendSharedDeepImports() {
  return {
    name: 'resolve-frontend-shared-deep-imports',
    resolveId(source) {
      if (!source.startsWith(FRONTEND_SHARED_DEEP_IMPORT)) {
        return null;
      }

      const subPath = source.slice('@hypothesis/frontend-shared/'.length);
      const base = path.resolve(FRONTEND_SHARED, subPath);

      const candidate = [base, `${base}.js`, path.join(base, 'index.js')].find(
        file => fs.existsSync(file) && fs.statSync(file).isFile(),
      );

      return candidate ?? null;
    },
  };
}

const isProd = process.env.NODE_ENV === 'production';
const prodPlugins = [];
if (isProd) {
  prodPlugins.push(terser());

  // Eliminate debug-only imports.
  prodPlugins.push(
    virtual({
      'preact/debug': '',
    }),
  );
}

function bundleConfig(name, entryFile) {
  return {
    input: {
      [name]: entryFile,
    },
    output: {
      dir: 'build/scripts/',
      format: 'es',
      chunkFileNames: '[name].bundle.js',
      entryFileNames: '[name].bundle.js',
    },
    // Suppress a warning (https://rollupjs.org/guide/en/#error-this-is-undefined)
    // due to https://github.com/babel/babel/issues/9149.
    //
    // Any code string other than "undefined" which evaluates to `undefined` will work here.
    context: 'void(0)',
    plugins: [
      replace({
        preventAssignment: true,
        values: {
          'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV),
        },
      }),
      babel({
        babelHelpers: 'bundled',
        exclude: 'node_modules/**',
        extensions: ['.js', '.ts', '.tsx'],
      }),
      resolveFrontendSharedDeepImports(),
      nodeResolve({
        extensions: ['.js', '.ts', '.tsx'],
      }),
      commonjs({ include: 'node_modules/**' }),
      ...prodPlugins,
    ],
  };
}

export default [
  bundleConfig('frontend_apps', 'lms/static/scripts/frontend_apps/index.tsx'),
  bundleConfig('browser_check', 'lms/static/scripts/browser_check/index.ts'),
  bundleConfig('ui-playground', 'lms/static/scripts/ui-playground/index.ts'),
];
