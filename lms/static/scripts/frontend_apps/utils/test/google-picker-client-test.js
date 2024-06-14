/* eslint-disable new-cap */
import { PickerCanceledError } from '../../errors';
import {
  GOOGLE_DRIVE_SCOPE,
  GooglePickerClient,
  $imports,
} from '../google-picker-client';

function createGoogleLibFakes() {
  let resolvePickerVisible;
  const pickerVisible = new Promise(
    resolve => (resolvePickerVisible = resolve),
  );

  const pickerBuilder = {
    addView: sinon.stub().returnsThis(),
    build: sinon.stub().returnsThis(),
    setCallback: sinon.stub().returnsThis(),
    setDeveloperKey: sinon.stub().returnsThis(),
    setMaxItems: sinon.stub().returnsThis(),
    setOAuthToken: sinon.stub().returnsThis(),
    setOrigin: sinon.stub().returnsThis(),
    setVisible: show => {
      if (show) {
        resolvePickerVisible();
      }
    },
  };

  const pickerView = {
    setMimeTypes: sinon.stub(),
  };

  const pickerLib = {
    Action: {
      PICKED: 'picked',
      CANCEL: 'cancel',
    },
    DocsUploadView: function () {},
    PickerBuilder: function () {
      return pickerBuilder;
    },
    DocsView: function () {
      return pickerView;
    },
    ViewId: {
      DOCS: 'docs',
    },
  };

  const client = {
    setToken: sinon.stub(),
    init: sinon.stub(),
    drive: {
      permissions: {
        create: sinon.stub(),
      },
    },
  };

  return {
    // Fakes
    client,
    picker: {
      api: pickerLib,
    },

    // Additional helpers for tests.
    pickerBuilder,
    pickerVisible,
  };
}

/**
 * Fake version of the TokenClient object returned by Google Identity Service's
 * `initTokenClient` function.
 *
 * See https://developers.google.com/identity/oauth2/web/reference/js-reference#TokenClient.
 */
class FakeTokenClient {
  constructor(config, authError) {
    this.config = config;
    this.requestAccessToken = sinon.stub().callsFake(() => {
      if (authError) {
        if (authError.useErrorCallback) {
          // Report a non-OAuth error
          this.config.error_callback(authError.response);
        } else {
          // Report an OAuth error
          this.config.callback(authError.response);
        }
      } else {
        this.config.callback({ access_token: 'the-access-token' });
      }
    });
  }
}

describe('GooglePickerClient', () => {
  // Authentication error to report when `requestAccessToken` method from
  // Google Identity Services library is called. Errors fall into two
  // categories, OAuth and non-OAuth errors. These are reported via different
  // JS callbacks. See FakeTokenClient.
  let authError;

  // FakeTokenClient created by most recent call to `initTokenClient`.
  let fakeTokenClient;

  let fakeLoadLibraries;
  let fakeGoogleLibs;

  function createClient({
    developerKey = 'john.developer',
    clientId = '12345',
    origin = 'https://eldorado.instructure.com',
  } = {}) {
    return new GooglePickerClient({
      developerKey,
      clientId,
      origin,
    });
  }

  beforeEach(() => {
    fakeGoogleLibs = createGoogleLibFakes();
    fakeLoadLibraries = sinon.stub().resolves(fakeGoogleLibs);

    const fakeIdentityServicesLibrary = {
      oauth2: {
        initTokenClient: config => {
          fakeTokenClient = new FakeTokenClient(config, authError);
          return fakeTokenClient;
        },
      },
    };

    $imports.$mock({
      './google-api-client': {
        loadIdentityServicesLibrary: async () => fakeIdentityServicesLibrary,
        loadLibraries: fakeLoadLibraries,
      },
    });
  });

  afterEach(() => {
    authError = null;
    $imports.$restore();
  });

  describe('#constructor', () => {
    it('loads Google API client', () => {
      createClient();
      assert.calledWith(fakeLoadLibraries, ['client', 'picker']);
    });
  });

  describe('#requestAuthorization', () => {
    it("requests the user's authorization to access their Google Drive files", async () => {
      const client = createClient();

      await client.requestAuthorization();

      assert.ok(fakeTokenClient);
      assert.match(fakeTokenClient.config, {
        client_id: '12345',
        scope: GOOGLE_DRIVE_SCOPE,
      });
      assert.calledOnce(fakeTokenClient.requestAccessToken);
    });

    it('does nothing if called a second time', async () => {
      const client = createClient();

      await client.requestAuthorization();

      const tokenClient = fakeTokenClient;
      await client.requestAuthorization();
      assert.equal(fakeTokenClient, tokenClient);

      assert.calledOnce(fakeTokenClient.requestAccessToken);
    });
  });

  describe('#showPicker', () => {
    it('requests authorization and sets token used by picker', async () => {
      const client = createClient();
      client.showPicker();

      await fakeGoogleLibs.pickerVisible;

      assert.ok(fakeTokenClient);
      const builder = fakeGoogleLibs.picker.api.PickerBuilder();
      assert.calledWith(builder.setOAuthToken, 'the-access-token');
    });

    it('initializes and shows the Google Picker', async () => {
      const client = createClient();
      client.showPicker();
      await fakeGoogleLibs.pickerVisible;
    });

    [
      ['https://foobar.instructure.com', 'https://foobar.instructure.com'],

      // If the `origin` value passed to the constructor is just a domain it
      // should be converted to a URL.
      ['foobar.instructure.com', 'https://foobar.instructure.com'],
    ].forEach(([origin, pickerOrigin]) => {
      it('sets the origin of the picker', async () => {
        const client = createClient({ origin });

        client.showPicker();
        await fakeGoogleLibs.pickerVisible;

        assert.calledWith(fakeGoogleLibs.pickerBuilder.setOrigin, pickerOrigin);
      });
    });

    it('rejects with a `PickerCanceledError` if the user cancels authorization', async () => {
      authError = {
        useErrorCallback: true,
        response: {
          type: 'popup_closed',
        },
      };

      const client = createClient();

      let err;
      try {
        await client.showPicker();
      } catch (e) {
        err = e;
      }

      assert.instanceOf(err, PickerCanceledError);
    });

    [
      {
        useErrorCallback: true,
        response: { type: 'popup_failed_to_open' },
        expectedMessage:
          'Showing Google authorization dialog failed: popup_failed_to_open',
      },
      {
        useErrorCallback: false,
        response: { error_description: 'Invalid client ID' },
        expectedMessage:
          'Getting Google access token failed: Invalid client ID',
      },
    ].forEach(({ useErrorCallback, response, expectedMessage }) => {
      it('rejects with the upstream Error if authorization fails for other reasons', async () => {
        authError = {
          useErrorCallback,
          response,
        };
        const client = createClient();

        let err;
        try {
          await client.showPicker();
        } catch (e) {
          err = e;
        }

        assert.equal(err.message, expectedMessage);
      });
    });

    it('resolves with the file ID and URL when a file is chosen', async () => {
      const client = createClient();
      let result = client.showPicker();

      await fakeGoogleLibs.pickerVisible;

      const pickerLib = fakeGoogleLibs.picker.api;
      const builder = pickerLib.PickerBuilder();
      const callback = builder.setCallback.getCall(0).callback;

      callback({
        action: pickerLib.Action.PICKED,
        docs: [{ id: 'doc1', name: 'Floops.pdf' }],
      });

      result = await result;
      assert.deepEqual(result, {
        id: 'doc1',
        name: 'Floops.pdf',
        url: 'https://drive.google.com/uc?id=doc1&export=download',
      });
    });

    it('includes resource key if file has one', async () => {
      const client = createClient();
      let result = client.showPicker();

      await fakeGoogleLibs.pickerVisible;

      const pickerLib = fakeGoogleLibs.picker.api;
      const builder = pickerLib.PickerBuilder();
      const callback = builder.setCallback.getCall(0).callback;

      callback({
        action: pickerLib.Action.PICKED,
        docs: [{ id: 'doc1', name: 'Flaps.pdf', resourceKey: 'thekey' }],
      });

      result = await result;
      assert.deepEqual(result, {
        id: 'doc1',
        name: 'Flaps.pdf',
        url: 'https://drive.google.com/uc?id=doc1&export=download&resourcekey=thekey',
      });
    });

    it('rejects with a `PickerCanceledError` if the picker is canceled', async () => {
      const client = createClient();
      const result = client.showPicker();

      await fakeGoogleLibs.pickerVisible;

      const pickerLib = fakeGoogleLibs.picker.api;
      const builder = pickerLib.PickerBuilder();
      const callback = builder.setCallback.getCall(0).callback;

      callback({ action: pickerLib.Action.CANCEL });

      let err;
      try {
        await result;
      } catch (e) {
        err = e;
      }

      assert.instanceOf(err, PickerCanceledError);
    });
  });

  describe('#enablePublicViewing', () => {
    let createPermission;

    beforeEach(() => {
      createPermission = fakeGoogleLibs.client.drive.permissions.create;
      const apiRequest = { then: resolve => resolve() };
      createPermission.returns(apiRequest);
    });

    it('initializes the Google Drive API client', async () => {
      const client = createClient();
      await client.requestAuthorization();
      await client.enablePublicViewing('doc1');

      assert.calledWith(fakeGoogleLibs.client.init, {
        apiKey: 'john.developer',
        discoveryDocs: [
          'https://www.googleapis.com/discovery/v1/apis/drive/v3/rest',
        ],
      });
    });

    it('throws error if access token has not been acquired', async () => {
      const client = createClient();

      let err;
      try {
        await client.enablePublicViewing('doc1');
      } catch (e) {
        err = e;
      }

      assert.instanceOf(err, Error);
      assert.equal(
        err.message,
        'Google Drive API access has not been authorized',
      );
    });

    it('updates the sharing settings of the file', async () => {
      const client = createClient();
      await client.requestAuthorization();
      await client.enablePublicViewing('doc1');

      assert.calledWith(createPermission, {
        fileId: 'doc1',
        resource: {
          role: 'reader',
          type: 'anyone',
        },
      });
    });

    it('rejects if changing the sharing settings fails', async () => {
      const client = createClient();
      await client.requestAuthorization();
      createPermission.returns({
        then: (_, reject) =>
          reject({
            result: {
              error: {
                message: 'Changing permissions failed',
              },
            },
          }),
      });
      let err;
      try {
        await client.enablePublicViewing('doc1');
      } catch (e) {
        err = e;
      }
      assert.equal(err.message, 'Changing permissions failed');
    });
  });
});
