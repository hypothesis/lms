import alias from '@rollup/plugin-alias';
import { babel } from '@rollup/plugin-babel';
import commonjs from '@rollup/plugin-commonjs';
import { nodeResolve } from '@rollup/plugin-node-resolve';
import replace from '@rollup/plugin-replace';
import { string } from 'rollup-plugin-string';
import { terser } from 'rollup-plugin-terser';
import virtual from '@rollup/plugin-virtual';

const isProd = process.env.NODE_ENV === 'production';
const prodPlugins = [];
if (isProd) {
  prodPlugins.push(terser());

  // Eliminate debug-only imports.
  prodPlugins.push(
    virtual({
      'preact/debug': '',
    })
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
    plugins: [
      alias({
        entries: [
          {
            // This is needed because of Babel configuration used by
            // @hypothesis/frontend-shared. It can be removed once that is fixed.
            find: 'preact/compat/jsx-dev-runtime',
            replacement: 'preact/jsx-dev-runtime',
          },
        ],
      }),
      replace({
        preventAssignment: true,
        values: {
          'process.env.NODE_ENV': process.env.NODE_ENV,
        },
      }),
      babel({
        babelHelpers: 'bundled',
        exclude: 'node_modules/**',
      }),
      nodeResolve(),
      commonjs({ include: 'node_modules/**' }),
      string({
        include: '**/*.svg',
      }),
      ...prodPlugins,
    ],
  };
}

export default [
  bundleConfig('frontend_apps', 'lms/static/scripts/frontend_apps/index.js'),
  bundleConfig(
    'new_application_instance',
    'lms/static/scripts/new-application-instance.js'
  ),
  bundleConfig('browser_check', 'lms/static/scripts/browser_check/index.js'),
  bundleConfig('ui-playground', 'lms/static/scripts/ui-playground/index.js'),
];
