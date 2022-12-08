import { PickerCanceledError } from '../errors';
import {
  loadLibraries,
  loadIdentityServicesLibrary,
} from './google-api-client';

export const GOOGLE_DRIVE_SCOPE = 'https://www.googleapis.com/auth/drive';

/**
 * Convert a domain (example.com) into a valid web origin (https://example.com).
 *
 * This is needed because the origin value may ultimately come from the
 * `custom_canvas_api_domain` LTI launch parameter on the backend, in which
 * case it may be a domain rather than a URL. If so, this should really be handled
 * on the backend.
 *
 * @param {string} origin
 */
function addHttps(origin) {
  if (origin.indexOf('://') !== -1) {
    return origin;
  }
  return 'https://' + origin;
}

/**
 * Subset of the `Document` type returned by the Google Picker.
 *
 * See https://developers.google.com/picker/docs/reference#document
 *
 * @typedef PickerDocument
 * @prop {string} id
 * @prop {string} name - Filename
 * @prop {string} url
 * @prop {string} [resourceKey] - A key which is present on a subset of older
 *   Google Drive files. If present this needs to be provided to various
 *   Google Drive APIs and share links (via the `resourcekey` query param).
 *
 *   As far as we understand, this key was added to old files to guard against
 *   their IDs being guessed.
 *
 *   See https://developers.google.com/drive/api/v3/resource-keys and
 *   https://support.google.com/drive/answer/10729743.
 */

/**
 * A wrapper around the Google Picker API client libraries.
 *
 * See https://developers.google.com/picker/ for documentation on the
 * underlying libraries.
 */
export class GooglePickerClient {
  /**
   * @param {object} options
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
    this._origin = addHttps(origin);

    const libs = loadLibraries(['client', 'picker']);

    this._identityServices = loadIdentityServicesLibrary();

    this._gapiClient = libs.then(({ client }) => client);
    this._gapiPicker = libs.then(({ picker }) => picker.api);

    /** @type {string|null} */
    this._accessToken = null;
  }

  /**
   * Authorize this application's access to the user's files in Google Drive.
   *
   * @return {Promise<string>} - An access token for making Google Drive API requests.
   *   The access token is cached for use in future Drive API calls.
   */
  async requestAuthorization() {
    if (this._accessToken) {
      return this._accessToken;
    }

    const idServices = await this._identityServices;

    /** @type {(err: Error) => void} */
    let rejectAccessToken;

    /** @type {(token: string) => void} */
    let resolveAccessToken;
    const accessToken = new Promise((resolve, reject) => {
      resolveAccessToken = resolve;
      rejectAccessToken = reject;
    });

    // See https://developers.google.com/identity/oauth2/web/reference/js-reference#CodeClientConfig.
    const client = idServices.oauth2.initTokenClient({
      client_id: this._clientId,
      scope: GOOGLE_DRIVE_SCOPE,

      // Callback used for successful responses and OAuth errors.
      callback: response => {
        if (response.access_token) {
          resolveAccessToken(response.access_token);
        } else {
          rejectAccessToken(
            new Error(
              `Getting Google access token failed: ${response.error_description}`
            )
          );
        }
      },

      // Callback used for non-OAuth errors.
      error_callback: response => {
        if (response.type === 'popup_closed') {
          rejectAccessToken(new PickerCanceledError());
        } else {
          rejectAccessToken(
            new Error(
              `Showing Google authorization dialog failed: ${response.type}`
            )
          );
        }
      },
    });

    client.requestAccessToken();

    const token = await accessToken;
    this._accessToken = token;
    return token;
  }

  /**
   * Show the Google file picker and return the document ID and
   * URL of the selected file.
   *
   * This will automatically call {@link requestAuthorization} to acquire
   * an access token.
   *
   * @return {Promise<{ id: string, name: string, url: string }>}
   *   Document ID, filename and download URL of the selected file.
   *   The download URL is only available by users who have access to the file.
   *   To make it accessible to everyone, use `enablePublicViewing`.
   */
  async showPicker() {
    const pickerLib = await this._gapiPicker;
    const accessToken = await this.requestAuthorization();

    /** @type {(doc: PickerDocument) => void} */
    let resolve;

    /** @type {(e: Error) => void} */
    let reject;

    /**
     * @param {object} args
     *   @param {string} args.action
     *   @param {PickerDocument[]} args.docs
     */
    function pickerCallback({ action, docs }) {
      if (action === pickerLib.Action.PICKED) {
        const doc = docs[0];
        // nb. It would be better to get this URL from Google Drive instead of
        // hardcoding it if possible.
        const url = new URL('https://drive.google.com/uc');
        url.searchParams.append('id', doc.id);
        url.searchParams.append('export', 'download');
        if (doc.resourceKey) {
          url.searchParams.append('resourcekey', doc.resourceKey);
        }
        resolve({ id: doc.id, name: doc.name, url: url.toString() });
      } else if (action === pickerLib.Action.CANCEL) {
        reject(new PickerCanceledError());
      }
    }

    const view = new pickerLib.View(pickerLib.ViewId.DOCS);
    view.setMimeTypes('application/pdf');
    const picker = new pickerLib.PickerBuilder()
      .addView(view)
      .addView(new pickerLib.DocsUploadView())
      .setCallback(pickerCallback)
      .setDeveloperKey(this._developerKey)
      .setMaxItems(1)
      .setOAuthToken(accessToken)
      .setOrigin(this._origin)
      .build();
    picker.setVisible(true);

    return new Promise((resolve_, reject_) => {
      resolve = resolve_;
      reject = reject_;
    });
  }

  /** Prepare Google API client library for making Google Drive API requests. */
  async _initAPIClient() {
    const gapiClient = await this._gapiClient;

    if (!this._accessToken) {
      throw new Error('Google Drive API access has not been authorized');
    }
    gapiClient.setToken({ access_token: this._accessToken });

    await gapiClient.init({
      apiKey: this._developerKey,
      discoveryDocs: [
        'https://www.googleapis.com/discovery/v1/apis/drive/v3/rest',
      ],
    });

    return gapiClient;
  }

  /**
   * Change the sharing settings on a document in Google Drive to make it
   * publicly viewable to anyone with the link.
   *
   * @param {string} docId
   */
  async enablePublicViewing(docId) {
    const gapiClient = await this._initAPIClient();
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
