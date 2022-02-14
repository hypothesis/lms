import { PickerCanceledError, PickerPermissionError } from '../errors';
import { loadOneDriveAPI } from './onedrive-api-client';

/**
 * Partial type for OneDrive share links.
 *
 * See https://docs.microsoft.com/en-us/graph/api/resources/sharinglink?view=graph-rest-1.0
 *
 * @typedef SharingLink
 * @prop {string} webUrl
 */

/**
 * Partial type for OneDrive item permissions.
 *
 * See https://docs.microsoft.com/en-us/graph/api/resources/permission?view=graph-rest-1.0
 *
 * @typedef Permission
 * @prop {SharingLink} link
 */

/**
 * Partial type for OneDrive items.
 *
 * See https://docs.microsoft.com/en-us/graph/api/resources/driveitem?view=graph-rest-1.0.
 *
 * @typedef DriveItem
 * @prop {string} name
 * @prop {Permission[]} permissions
 */

/**
 * Result of successful file picker response.
 *
 * This property is not present if the OneDrive sharing policies don't allow
 * sharing files publicly (using links that don't require sign-in).
 * See https://hypothes-is.slack.com/archives/C2BLQDKHA/p1643309746775569
 *
 * See https://docs.microsoft.com/en-us/onedrive/developer/controls/file-pickers/js-v72/open-file?view=odsp-graph-online#4-handling-the-picker-response-object.
 *
 * @typedef PickerResponse
 * @prop {DriveItem[]} [value]
 */

/**
 * A wrapper around the Microsoft OneDrive file picker.
 *
 * See https://docs.microsoft.com/en-us/onedrive/developer/controls/file-pickers/js-v72/open-file?view=odsp-graph-online
 * for documentation on the underlying library. The picker is built on the
 * Microsoft Graph API and responses etc. use types associated with that API.
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
      /** @param {PickerResponse} result */
      const success = result => {
        try {
          // @ts-expect-error
          const driveItem = result.value[0];
          try {
            const name = driveItem.name;
            const sharingURL = driveItem.permissions[0].link.webUrl;
            const url = OneDrivePickerClient.downloadURL(sharingURL);
            resolve({ name, url });
          } catch (error) {
            reject(error);
          }
        } catch {
          reject(new PickerPermissionError());
        }
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
