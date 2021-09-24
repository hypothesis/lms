import { loadOneDriveAPI } from './onedrive-api-client';
import { PickerCanceledError } from './google-picker-client';

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
   * @returns Promise<{url: string}> - the URL of the file
   * @throws {Error} - there are two types of errors:
   *   - PickerCancelledError: raise when the user cancels the OneDrive dialog picker
   *   - Other errors: raise when (1) the OneDrive client fails to load (`window.OneDrive` is
   *       undefined), or when (2) the picker fails in a different way.
   */
  async showPicker() {
    return new Promise((resolve, reject) => {
      const success = (/** @type {any} */ file) => {
        const sharingURL = file.value[0].permissions[0].link.webUrl;
        const url = OneDrivePickerClient.encodeSharingURL(sharingURL);
        resolve({ url });
      };
      const cancel = () => reject(new PickerCanceledError());
      const error = (/** @type {Error} */ error) => reject(error);
      window.OneDrive.open({
        ...this._filePickerOptions,
        ...{ success, cancel, error },
      });
    });
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
