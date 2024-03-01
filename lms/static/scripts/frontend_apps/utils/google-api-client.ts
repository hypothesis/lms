/**
 * Load the Google Identity Services client library, if not already loaded.
 *
 * See https://developers.google.com/identity/oauth2/web/guides/load-3p-authorization-library.
 */
export async function loadIdentityServicesLibrary(): Promise<
  typeof window.google.accounts
> {
  // The third-party types assume `window.google` always exists, but it is only
  // set once the library is loaded.
  //
  // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
  if (window.google?.accounts) {
    return window.google.accounts;
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.onload = () => {
      resolve(window.google.accounts);
    };
    script.onerror = () => {
      reject(new Error('Failed to load Google Identity Services client'));
    };
    document.body.appendChild(script);
  });
}

/**
 * Load the Google API loader script (`window.gapi`), if not already loaded.
 */
async function loadGAPI(): Promise<typeof window.gapi> {
  // The third-party types assume `window.gapi` always exists, but it is only
  // set once the library is loaded.
  //
  // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
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
 * @return
 *   The `gapi` object with properties corresponding to each of the named
 *   libraries' entry points.
 */
export async function loadLibraries(
  names: string[],
): Promise<Record<string, any>> {
  const gapi = await loadGAPI();

  return new Promise((resolve, reject) => {
    gapi.load(names.join(':'), {
      callback: () => {
        resolve(gapi);
      },

      onerror: (err: any) => {
        reject(err);
      },
    });
  });
}
