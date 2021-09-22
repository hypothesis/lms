import { loadOneDriveAPI } from './onedrive-api-client';

export class OneDrivePickerClient {
  /**
   * @param {object} options
   * @param {string} options.clientId
   * @param {string} options.redirectURI - the URL that is used to launch the picker
   */
  constructor({ clientId, redirectURI }) {
    loadOneDriveAPI();

    this._filePickerOptions = {
      clientId,
      action: 'share',
      multiSelect: false,
      viewType: 'files', // The type of item that can be selected.
      advanced: {
        redirectUri: redirectURI,
        filter: '.pdf',
        createLinkParameters: { type: 'view', scope: 'anonymous' },
      },
    };
  }

  /**
   * Opens the OneDrive picker
   *
   * @param {{success?: (file: any) => void, cancel?: () => void, error?: (e: Error) => void}} callbacks
   * @throws {Error} - if the OneDrive client failed to load and hence
   *   `window.OneDrive` is undefined
   */
  showPicker(callbacks = {}) {
    window.OneDrive.open({ ...this._filePickerOptions, ...callbacks });
  }

  /**
   * Encode sharing URL according to the MS specification
   * https://docs.microsoft.com/en-us/graph/api/shares-get?view=graph-rest-1.0&tabs=http#encoding-sharing-urls
   * 1. Use base64 encode the URL.
   * 2. Convert the base64 encoded result to unpadded base64url format by
   *   removing '=' characters from the end of the value, replacing '/'
   *   with '_' and '+' with '-'
   * 3. Append u! to be beginning of the string.
   *
   * @param {string} sharingURL
   */
  static encodeSharingURL(sharingURL) {
    const b64SharedLink = btoa(sharingURL)
      .replace(/=/g, '')
      .replace(/\//g, '_')
      .replace(/\+/g, '-');
    // Append u! to be beginning of the string.
    return `https://api.onedrive.com/v1.0/shares/u!${b64SharedLink}/root/content`;
  }
}
