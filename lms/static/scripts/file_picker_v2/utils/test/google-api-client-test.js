import { loadLibraries } from '../google-api-client';

describe('loadLibraries', () => {
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
  });

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
    dummyScript.onerror({ error: new Error('Script failed to load') });

    let err;
    try {
      await libs;
    } catch (e) {
      err = e;
    }
    assert.equal(err.message, 'Script failed to load');
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
