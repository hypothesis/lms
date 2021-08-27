/* eslint-disable new-cap */

import {
  GOOGLE_DRIVE_SCOPE,
  GooglePickerClient,
  PickerCanceledError,
  $imports,
} from '../google-picker-client';

function createGoogleLibFakes() {
  let resolvePickerVisible;
  const pickerVisible = new Promise(
    resolve => (resolvePickerVisible = resolve)
  );

  const user = {
    getAuthResponse: sinon
      .stub()
      .resolves({ access_token: 'the-access-token' }),
  };

  const googleAuth = {
    signIn: sinon.stub().resolves(user),
  };

  const auth2 = {
    init: sinon.stub().returns(googleAuth),
  };

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
    View: function () {
      return pickerView;
    },
    ViewId: {
      DOCS: 'docs',
    },
  };

  const client = {
    init: sinon.stub(),
    drive: {
      permissions: {
        create: sinon.stub(),
      },
    },
  };

  return {
    // Fakes
    auth2,
    client,
    picker: {
      api: pickerLib,
    },

    // Additional helpers for tests.
    pickerBuilder,
    pickerVisible,
  };
}

describe('GooglePickerClient', () => {
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

    $imports.$mock({
      './google-api-client': {
        loadLibraries: fakeLoadLibraries,
      },
    });
  });

  describe('#constructor', () => {
    it('loads Google API client', async () => {
      createClient();
      assert.calledWith(fakeLoadLibraries, ['auth2', 'client', 'picker']);
    });
  });

  describe('#showPicker', () => {
    it("requests the user's authorization to access their Google Drive files", async () => {
      const client = createClient();
      client.showPicker();

      await fakeGoogleLibs.pickerVisible;

      assert.calledWith(fakeGoogleLibs.auth2.init, {
        client_id: '12345',
        scope: GOOGLE_DRIVE_SCOPE,
      });
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
      const client = createClient();
      const auth = fakeGoogleLibs.auth2.init();
      auth.signIn.rejects({ error: 'popup_closed_by_user' });

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
        makeError: () => ({ error: 'something-went-wrong' }),
        expectedMessage: 'something-went-wrong',
      },
      {
        makeError: () => new Error('Something failed'),
        expectedMessage: 'Something failed',
      },
    ].forEach(({ makeError, expectedMessage }) => {
      it('rejects with the upstream Error if authorization fails for other reasons', async () => {
        const client = createClient();
        const auth = fakeGoogleLibs.auth2.init();
        auth.signIn.rejects(makeError());

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

      callback({ action: pickerLib.Action.PICKED, docs: [{ id: 'doc1' }] });

      result = await result;
      assert.deepEqual(result, {
        id: 'doc1',
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
        docs: [{ id: 'doc1', resourceKey: 'thekey' }],
      });

      result = await result;
      assert.deepEqual(result, {
        id: 'doc1',
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
      const apiRequest = { execute: resolve => resolve() };
      createPermission.returns(apiRequest);
    });

    it('initializes the Google Drive API client', async () => {
      const client = createClient();
      await client.enablePublicViewing('doc1');

      assert.calledWith(fakeGoogleLibs.client.init, {
        apiKey: 'john.developer',
        clientId: '12345',
        discoveryDocs: [
          'https://www.googleapis.com/discovery/v1/apis/drive/v3/rest',
        ],
        scope: GOOGLE_DRIVE_SCOPE,
      });
    });

    it('updates the sharing settings of the file', async () => {
      const client = createClient();
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
      createPermission.returns({
        execute: (_, reject) =>
          reject(new Error('Changing permissions failed')),
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
