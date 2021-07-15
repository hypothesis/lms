/**
 * Manages an LMS authentication popup window.
 */
export default class AuthWindow {
  /**
   * @param {Object} options
   * @param {string} options.authToken -
   *   Authorization token used for API requests between frontend and backend
   * @param {string} options.authUrl -
   *   The initial URL to open in the authorization popup
   */
  constructor({ authToken, authUrl }) {
    this._authToken = authToken;
    this._authUrl = authUrl;
  }

  close() {
    if (this._authWin) {
      this._authWin.close();
      this._authWin = null;
    }
  }

  focus() {
    if (this._authWin) {
      this._authWin.focus();
    }
  }

  /**
   * Show the authorization window and wait for it to be closed, which happens
   * either when authorization is completed or if the user manually closes
   * the window.
   *
   * In order to check the authorization status after the window closes, make
   * an API call and check for a successful response.
   * @returns {Promise<void>}
   */
  async authorize() {
    const width = 775;
    const height = 560;
    const left = Math.round(window.screen.width / 2 - width / 2);
    const top = Math.round(window.screen.height / 2 - height / 2);
    const settings = `left=${left},top=${top},width=${width},height=${height}`;

    const params = new URLSearchParams();
    params.set('authorization', this._authToken);
    const authUrl = `${this._authUrl}?${params}`;

    this._authWin = window.open(
      authUrl,
      `Allow access to Canvas files`,
      settings
    );

    if (!this._authWin) {
      throw new Error('Window creation failed');
    }

    return new Promise(resolve => {
      const timer = setInterval(() => {
        if (!this._authWin || this._authWin.closed) {
          clearInterval(timer);
          resolve();
        }
      }, 300);
    });
  }
}
