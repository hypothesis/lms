'use strict';

const fs = require('fs');
const path = require('path');

const autoprefixer = require('autoprefixer');
const postcss = require('postcss');
const sass = require('sass');

/**
 * @typedef Options
 * @prop {string} input - Input file path
 * @prop {boolean} minify - Whether to minify the generated bundle
 * @prop {string} output - Output file path
 */

/**
 * Compile a SASS file and postprocess the result.
 *
 * @param {Options} options - Object specifying the input and output paths and
 *                  whether to minify the result.
 * @return {Promise} Promise for completion of the build.
 */
async function compileSass({ input, minify, output }) {
  const sourcemapPath = output + '.map';

  let result = sass.renderSync({
    file: input,
    includePaths: [path.dirname(input), 'node_modules'],
    outputStyle: minify ? 'compressed' : 'expanded',
    sourceMap: sourcemapPath,
  });

  const postcssPlugins = [autoprefixer];
  result = await postcss(postcssPlugins).process(result.css, {
    from: output,
    to: output,
    map: {
      inline: false,
      prev: result.map.toString(),
    },
  });

  fs.writeFileSync(output, result.css);
  fs.writeFileSync(sourcemapPath, result.map.toString());
}

module.exports = compileSass;
