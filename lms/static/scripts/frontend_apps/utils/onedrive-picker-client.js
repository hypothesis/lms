import { PickerCanceledError } from '../errors';
import { loadOneDriveAPI } from './onedrive-api-client';

/**
 * A wrapper around the Microsoft OneDrive file picker.
 *
 * See https://docs.microsoft.com/en-us/onedrive/developer/controls/file-pickers/js-v72/open-file?view=odsp-graph-online
 * for documentation on the underlying library.
 */
export class OneDrivePickerClient {
  /**
   * @param {object} options
   * @param {string} options.clientId
   * @param {string} options.redirectURI - the URL that is used to launch the picker
   */
  constructor({ clientId, redirectURI }) {
    this._oneDriveAPI = loadOneDriveAPI();
    this._clientId = clientId;
    this._redirectURI = redirectURI;
  }

  /**
   * Opens the OneDrive picker
   *
   * @return {Promise<{ name: string, url: string }>} The (file) name and URL
   * @throws {Error} - there are two types of errors:
   *   - PickerCancelledError: raised when the user cancels the OneDrive dialog picker
   *   - Error: raised when (1) the OneDrive client fails to load, or when (2)
   *       the picker fails with internal or backend problem.
   */
  async showPicker() {
    const oneDrive = await this._oneDriveAPI;
    return new Promise((resolve, reject) => {
      const success = (/** @type {any} */ file) => {
        const name = file.value[0].name;
        const sharingURL = file.value[0].permissions[0].link.webUrl;
        const url = OneDrivePickerClient.downloadURL(sharingURL);
        resolve({ name, url });
      };
      const cancel = () => reject(new PickerCanceledError());
      const error = (/** @type {Error} */ error) => reject(error);

      const filePickerOptions = {
        clientId: this._clientId,
        action: 'share',
        multiSelect: false,
        viewType: 'files', // The type of item that can be selected.
        advanced: {
          redirectUri: this._redirectURI,
          filter: '.pdf',
          createLinkParameters: { type: 'view', scope: 'anonymous' },
        },
        success,
        cancel,
        error,
      };
      oneDrive.open(filePickerOptions);
    });
  }

  /**
   * Creates a direct download URL from the sharing one.
   *
   * For sharepoint URLs just append "?download=1" to the provided URL.
   *
   * For OneDrive URLs encode sharing URL according to the MS specification:
   *
   * https://docs.microsoft.com/en-us/graph/api/shares-get?view=graph-rest-1.0&tabs=http#encoding-sharing-urls
   * 1. Use base64 encode the URL.
   * 2. Convert the base64 encoded result to unpadded base64url format by
   *   removing '=' characters from the end of the value, replacing '/'
   *   with '_' and '+' with '-'
   * 3. Append u! to be beginning of the string.
   *
   * @param {string} sharingURL
   */
  static downloadURL(sharingURL) {
    const url = new URL(sharingURL);
    if (url.hostname.endsWith('sharepoint.com')) {
      url.search = 'download=1';
      return url.href;
    } else {
      const b64SharedLink = btoa(sharingURL)
        .replace(/=/g, '')
        .replace(/\//g, '_')
        .replace(/\+/g, '-');
      // Append u! to be beginning of the string.
      return `https://api.onedrive.com/v1.0/shares/u!${b64SharedLink}/root/content`;
    }
  }
}
