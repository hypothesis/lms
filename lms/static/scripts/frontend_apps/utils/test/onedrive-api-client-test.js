import { loadOneDriveAPI } from '../onedrive-api-client';

describe('loadOneDriveAPI', () => {
  let fakeScriptElement;

  beforeEach(() => {
    // Prevent the tests from making a real network request to load the real
    // script.
    fakeScriptElement = document.createElement('fake-script');
    sinon.stub(document, 'createElement').returns(fakeScriptElement);
    delete window.OneDrive;
  });

  afterEach(() => {
    document.createElement.restore();
    fakeScriptElement.remove();
    delete window.OneDrive;
  });

  it('resolves if OneDrive script loads', async () => {
    const onLoad = loadOneDriveAPI();
    const options = { option: 'dummy' };

    // Simulate successful script loading.
    window.OneDrive = {
      open: sinon.stub(),
    };
    fakeScriptElement.dispatchEvent(new Event('load'));
    const oneDrive = await onLoad;
    oneDrive.open(options);

    assert.exists(fakeScriptElement.src);
    assert.calledOnce(window.OneDrive.open);
    assert.calledWith(window.OneDrive.open, options);
  });

  it('throws an error if OneDrive script fails to load', async () => {
    const onLoad = loadOneDriveAPI();
    let expectedError;

    // Simulate unsuccessful script loading.
    fakeScriptElement.dispatchEvent(new Event('error'));
    try {
      await onLoad;
    } catch (error) {
      expectedError = error;
    }

    assert.exists(fakeScriptElement.src);
    assert.equal(expectedError.message, 'Failed to load OneDrive API');
  });

  it('immediately returns OneDrive if previously loaded', async () => {
    // Set `window.OneDrive` before calling `loadOneDriveAPI` as if the loading
    // has already happened.
    window.OneDrive = {
      open: sinon.stub(),
    };
    const options = { option: 'dummy' };

    const oneDrive = await loadOneDriveAPI();
    oneDrive.open(options);

    assert.calledOnce(window.OneDrive.open);
    assert.calledWith(window.OneDrive.open, options);
    assert.notCalled(document.createElement);
  });
});
