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
 */
function addHTTPS(origin: string) {
  if (origin.indexOf('://') !== -1) {
    return origin;
  }
  return 'https://' + origin;
}

/**
 * `Document` type returned by the Google Picker.
 *
 * See https://developers.google.com/picker/docs/reference#document
 */
export type PickerDocument = {
  id: string;

  /** Filename of document. */
  name: string;

  url: string;

  /**
   * A key which is present on a subset of older Google Drive files. If present
   * this needs to be provided to various Google Drive APIs and share links (via
   * the `resourcekey` query param).
   *
   * As far as we understand, this key was added to old files to guard against
   * their IDs being guessed.
   *
   * See https://developers.google.com/drive/api/v3/resource-keys and
   * https://support.google.com/drive/answer/10729743.
   */
  resourceKey?: string;
};

export type GooglePickerOptions = {
  /** API key obtained from the Google API console. */
  developerKey: string;

  /** Client ID obtained from the Google API console. */
  clientId: string;

  /**
   * The origin of the top-most page in the frame where this picker will
   * be served. This is needed when the picker is served inside an iframe
   * with a different origin than the top-level page
   */
  origin: string;
};

/**
 * A wrapper around the Google Picker API client libraries.
 *
 * See https://developers.google.com/picker/ for documentation on the
 * underlying libraries.
 */
export class GooglePickerClient {
  private _accessToken: string | null;
  private _clientId: string;
  private _developerKey: string;
  private _gapiClient: Promise<typeof gapi.client>;
  private _gapiPicker: Promise<typeof google.picker>;
  private _identityServices: Promise<typeof google.accounts>;
  private _origin: string;

  constructor({ developerKey, clientId, origin }: GooglePickerOptions) {
    this._accessToken = null;
    this._clientId = clientId;
    this._developerKey = developerKey;
    this._origin = addHTTPS(origin);

    this._identityServices = loadIdentityServicesLibrary();

    const libs = loadLibraries(['client', 'picker']);
    this._gapiClient = libs.then(({ client }) => client);
    this._gapiPicker = libs.then(({ picker }) => picker.api);
  }

  /**
   * Authorize this application's access to the user's files in Google Drive.
   *
   * @return An access token for making Google Drive API requests. The access
   *   token is cached for use in future Drive API calls.
   */
  async requestAuthorization(): Promise<string> {
    if (this._accessToken) {
      return this._accessToken;
    }

    const idServices = await this._identityServices;

    let rejectAccessToken: (err: Error) => void;
    let resolveAccessToken: (token: string) => void;

    const accessToken = new Promise<string>((resolve, reject) => {
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
              `Getting Google access token failed: ${response.error_description}`,
            ),
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
              `Showing Google authorization dialog failed: ${response.type}`,
            ),
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
   * @return
   *   Document ID, filename and download URL of the selected file.
   *   The download URL is only available by users who have access to the file.
   *   To make it accessible to everyone, use `enablePublicViewing`.
   */
  async showPicker(): Promise<{ id: string; name: string; url: string }> {
    const pickerLib = await this._gapiPicker;
    const accessToken = await this.requestAuthorization();

    let resolve: (doc: PickerDocument) => void;

    let reject: (e: Error) => void;

    function pickerCallback({
      action,
      docs,
    }: {
      action: string;
      docs: PickerDocument[];
    }) {
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

    const view = new pickerLib.DocsView(pickerLib.ViewId.DOCS);
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
  private async _initAPIClient() {
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
   */
  async enablePublicViewing(docId: string): Promise<void> {
    const gapiClient = await this._initAPIClient();
    const body = {
      type: 'anyone',
      role: 'reader',
    };
    // @ts-expect-error - We're missing types for `gapiClient.drive`.
    const request: unknown = gapiClient.drive.permissions.create({
      fileId: docId,
      resource: body,
    });
    const result = new Promise((resolve, reject) => {
      // @ts-expect-error - We're missing types for this, but see
      // https://github.com/google/google-api-javascript-client/blob/96cf6057f03c5e56179e83869828a06c47ce571b/docs/reference.md.
      //
      // For the types of arguments passed to resolve/reject, see
      // https://github.com/google/google-api-javascript-client/blob/96cf6057f03c5e56179e83869828a06c47ce571b/docs/promises.md#using-promises-1.
      request.then(resolve, reject);
    });

    try {
      await result;
    } catch (response) {
      throw new Error(
        response.result?.error?.message ?? 'Unable to make file public',
      );
    }
  }
}
