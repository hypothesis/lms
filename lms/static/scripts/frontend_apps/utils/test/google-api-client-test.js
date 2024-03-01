import {
  loadLibraries,
  loadIdentityServicesLibrary,
} from '../google-api-client';

describe('google-api-client', () => {
  let dummyScript;

  beforeEach(() => {
    // Prevent the tests from making a real network request to load the real
    // script.
    dummyScript = document.createElement('fake-script');
    sinon.stub(document, 'createElement').returns(dummyScript);
    delete window.gapi;
  });

  afterEach(() => {
    document.createElement.restore();
    dummyScript.remove();

    // Unset globals that Google API scripts would create.
    delete window.gapi;
    delete window.google;
  });

  describe('loadIdentityServicesLibrary', () => {
    it('loads API script', async () => {
      const libPromise = loadIdentityServicesLibrary();

      // Simulate script load completing.
      window.google = { accounts: {} };
      dummyScript.dispatchEvent(new Event('load'));

      const lib = await libPromise;

      assert.equal(dummyScript.src, 'https://accounts.google.com/gsi/client');
      assert.equal(lib, window.google.accounts);
    });

    it('does not load script if already loaded', async () => {
      window.google = { accounts: {} };
      const lib = await loadIdentityServicesLibrary();
      assert.notCalled(document.createElement);
      assert.equal(lib, window.google.accounts);
    });

    it('rejects if API script fails to load', async () => {
      const lib = loadIdentityServicesLibrary();

      // Simulate script failing to load.
      dummyScript.onerror();

      let err;
      try {
        await lib;
      } catch (e) {
        err = e;
      }
      assert.equal(
        err.message,
        'Failed to load Google Identity Services client',
      );
    });
  });

  describe('loadLibraries', () => {
    it('loads API script', async () => {
      // Call `loadLibraries` before `window.gapi` is set. This will cause
      // it to load the API script first.
      const libs = loadLibraries(['test']);
      window.gapi = {
        load: sinon.stub().callsFake((libs, { callback }) => {
          callback();
        }),
      };
      // Simulate API script load completing.
      dummyScript.dispatchEvent(new Event('load'));
      await libs;
    });

    it('loads requested Google client libraries', async () => {
      // Set `window.gapi` before calling `loadLibraries` as if API script had
      // already been loaded.
      window.gapi = {
        load: sinon.stub().callsFake((libs, { callback }) => {
          callback();
        }),
      };
      await loadLibraries(['one', 'two']);
      assert.calledWith(window.gapi.load, 'one:two');
    });

    it('rejects if API script fails to load', async () => {
      const libs = loadLibraries(['one', 'two']);

      // Simulate api.js failing to load.
      dummyScript.onerror();

      let err;
      try {
        await libs;
      } catch (e) {
        err = e;
      }
      assert.equal(err.message, 'Failed to load Google API client');
    });

    it('rejects if loading requested libraries fails', async () => {
      window.gapi = {
        load: sinon.stub().callsFake((libs, { onerror }) => {
          onerror(new Error('Loading failed'));
        }),
      };

      const libs = loadLibraries(['one', 'two']);
      dummyScript.dispatchEvent(new Event('load'));
      let err;
      try {
        await libs;
      } catch (e) {
        err = e;
      }

      assert.equal(err.message, 'Loading failed');
    });
  });
});
