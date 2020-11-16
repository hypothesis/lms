/**
 * Load the Google API loader script (`window.gapi`), if not already loaded.
 */
async function loadGAPI() {
  if (window.gapi) {
    return window.gapi;
  }

  return new Promise((resolve, reject) => {
    const gapiScript = document.createElement('script');
    gapiScript.src = 'https://apis.google.com/js/api.js';
    gapiScript.onload = () => {
      resolve(window.gapi);
    };
    gapiScript.onerror = () => {
      reject(new Error('Failed to load Google API client'));
    };
    document.body.appendChild(gapiScript);
  });
}

/**
 * Load the Google API client libraries with the given names.
 *
 * See https://developers.google.com/api-client-library/javascript/reference/referencedocs
 *
 * @param {string[]} names
 * @return {Promise<Record<string, any>>}
 *   The `gapi` object with properties corresponding to each of the named
 *   libraries' entry points.
 */
async function loadLibraries(names) {
  const gapi = await loadGAPI();

  return new Promise((resolve, reject) => {
    gapi.load(names.join(':'), {
      callback: () => {
        resolve(gapi);
      },

      /** @param {any} err */
      onerror: err => {
        reject(err);
      },
    });
  });
}

// Separate function declaration from export to work around
// https://github.com/robertknight/babel-plugin-mockable-imports/issues/9.
export { loadLibraries };
