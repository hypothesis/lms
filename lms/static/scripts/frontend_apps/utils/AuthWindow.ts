export type Options = {
  /** Authorization token used for API requests between frontend and backend. */
  authToken: string;

  /** The initial URL to open in the authorization popup. */
  authUrl: string;
};

/**
 * Manages an LMS authentication popup window.
 */
export default class AuthWindow {
  private _authToken: string;
  private _authURL: string;
  private _authWin: Window | null;

  constructor({ authToken, authUrl }: Options) {
    this._authToken = authToken;
    this._authURL = authUrl;
    this._authWin = null;
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
  async authorize(): Promise<void> {
    const width = 775;
    const height = 560;
    const left = Math.round(window.screen.width / 2 - width / 2);
    const top = Math.round(window.screen.height / 2 - height / 2);
    const settings = `left=${left},top=${top},width=${width},height=${height}`;

    const authURL = new URL(this._authURL);
    authURL.searchParams.set('authorization', this._authToken);

    this._authWin = window.open(
      authURL.toString(),
      `Allow access to Canvas files`,
      settings,
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
