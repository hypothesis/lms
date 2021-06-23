async function loadOneDriveAPI() {
  if (window.odapi) {
    return window.odapi;
  }

  return new Promise((resolve, reject) => {
    const oneDriveScript = document.createElement('script');
    oneDriveScript.src = 'https://js.live.net/v7.2/OneDrive.js';
    oneDriveScript.onload = () => {
      resolve(window.odapi);
    };
    oneDriveScript.onerror = () => {
      reject(new Error('Failed to load One Drive API client'));
    };
    document.body.appendChild(oneDriveScript);
  });
}

// Separate function declaration from export to work around
// https://github.com/robertknight/babel-plugin-mockable-imports/issues/9.
export { loadOneDriveAPI };
