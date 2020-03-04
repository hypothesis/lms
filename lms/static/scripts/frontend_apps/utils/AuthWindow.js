import queryString from 'query-string';

/**
 * Manages an LMS authentication popup window.
 */
export default class AuthWindow {
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
   */
  async authorize() {
    const width = 775;
    const height = 475;
    const left = Math.round(window.screen.width / 2 - width / 2);
    const top = Math.round(window.screen.height / 2 - height / 2);
    const settings = queryString
      .stringify({ left, top, width, height })
      .replace(/&/g, ',');
    const authQuery = queryString.stringify({ authorization: this._authToken });
    const authUrl = `${this._authUrl}?${authQuery}`;
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
