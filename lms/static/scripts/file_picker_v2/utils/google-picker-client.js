import { loadLibraries } from './google-api-client';

export const GOOGLE_DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive';

function addHttps(origin) {
  if (origin.indexOf('://') !== -1) {
    return origin;
  }
  return 'https://' + origin;
}

/**
 * Error thrown when the user cancels file selection.
 */
export class PickerCanceledError extends Error {
  constructor() {
    super('Dialog was canceled');
  }
}

/**
 * A wrapper around the Google Picker API client libraries.
 *
 * See https://developers.google.com/picker/ for documentation on the
 * underlying libraries.
 */
export class GooglePickerClient {
  /**
   * @param {Object} options
   * @param {string} options.developerKey -
   *   API key obtained from the Google API console.
   * @param {string} options.clientId -
   *   Client ID obtained from the Google API console.
   * @param {string} options.origin -
   *   The origin of the top-most page in the frame where this picker will
   *   be served. This is needed when the picker is served inside an iframe
   *   with a different origin than the top-level page
   */
  constructor({ developerKey, clientId, origin }) {
    this._clientId = clientId;
    this._developerKey = developerKey;
    this._origin = origin;

    const libs = loadLibraries(['auth2', 'client', 'picker']);

    this._gapiAuth2 = libs.then(({ auth2 }) => auth2);
    this._gapiClient = libs.then(({ client }) => client);
    this._gapiPicker = libs.then(({ picker }) => picker.api);
  }

  /**
   * Authorize this application's access to the user's files in Google Drive.
   *
   * @return {Promise<string>} - An access token for making Google Drive API requests.
   */
  async _authorizeDriveAccess() {
    const auth2 = await this._gapiAuth2;
    const googleAuth = auth2.init({
      client_id: this._clientId,
      scope: GOOGLE_DRIVE_SCOPE,
    });

    const user = await googleAuth.signIn();
    const authResponse = await user.getAuthResponse();
    return authResponse.access_token;
  }

  /**
   * Show the Google file picker and return the document ID and
   * URL of the selected file.
   *
   * @return {Promise<{ id: string, url: string }>}
   *   Document ID and download URL of the selected file. The download URL is
   *   only available by users who have access to the file. To make it accessible
   *   to everyone, use `enablePublicViewing`.
   */
  async showPicker() {
    const pickerLib = await this._gapiPicker;
    let accessToken;
    try {
      accessToken = await this._authorizeDriveAccess();
    } catch (err) {
      if (err.error === 'popup_closed_by_user') {
        throw new PickerCanceledError();
      } else if (err.error) {
        // Error returned by the Google API client (not an instance of `Error`)
        throw new Error(err.error);
      } else {
        throw err;
      }
    }

    let resolve;
    let reject;

    function pickerCallback({ action, docs }) {
      if (action === pickerLib.Action.PICKED) {
        const doc = docs[0];
        // TODO - Can we get this URL from Google Drive instead of hardcoding
        // it here?
        const url = `https://drive.google.com/uc?id=${doc.id}&export=download`;
        resolve({ id: doc.id, url });
      } else if (action === pickerLib.Action.CANCEL) {
        reject(new PickerCanceledError());
      }
    }

    const view = new pickerLib.View(pickerLib.ViewId.DOCS);
    view.setMimeTypes('application/pdf');
    const picker = new pickerLib.PickerBuilder()
      .addView(new pickerLib.DocsUploadView())
      .addView(view)
      .setCallback(pickerCallback)
      .setDeveloperKey(this._developerKey)
      .setMaxItems(1)
      .setOAuthToken(accessToken)
      .setOrigin(addHttps(this._origin))
      .build();
    picker.setVisible(true);

    return new Promise((resolve_, reject_) => {
      resolve = resolve_;
      reject = reject_;
    });
  }

  /**
   * Change the sharing settings on a document in Google Drive to make it
   * publicly viewable to anyone with the link.
   */
  async enablePublicViewing(docId) {
    const gapiClient = await this._gapiClient;

    // Prepare Google API client library for making Google Drive API requests.
    await gapiClient.init({
      apiKey: this._developerKey,
      clientId: this._clientId,
      discoveryDocs: [
        'https://www.googleapis.com/discovery/v1/apis/drive/v3/rest',
      ],
      scope: GOOGLE_DRIVE_SCOPE,
    });

    const body = {
      type: 'anyone',
      role: 'reader',
    };
    const request = gapiClient.drive.permissions.create({
      fileId: docId,
      resource: body,
    });
    return new Promise((resolve, reject) => {
      request.execute(resolve, reject);
    });
  }
}
