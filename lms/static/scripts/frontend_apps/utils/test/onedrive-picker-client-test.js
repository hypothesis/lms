import { OneDrivePickerClient, $imports } from '../onedrive-picker-client';

describe('OneDrivePickerClient', () => {
  let fakeLoadOneDriveAPI;

  function createClient({
    clientId = '12345',
    redirectURI = 'https://redirect.uri',
  } = {}) {
    return new OneDrivePickerClient({ clientId, redirectURI });
  }

  beforeEach(() => {
    fakeLoadOneDriveAPI = sinon.stub();

    $imports.$mock({
      './onedrive-api-client': {
        loadOneDriveAPI: fakeLoadOneDriveAPI,
      },
    });
    delete window.OneDrive;
  });

  afterEach(() => {
    $imports.$restore();
    delete window.OneDrive;
  });
  describe('#constructor', () => {
    it('calls `loadOneDriveAPI`', () => {
      createClient();

      // If `loadOneDriveAPI` fails to load the OneDrive client it raises an
      // unhandled rejection, which possible to emulate and catch on a test but
      // difficult hide from the output.
      assert.calledOnce(fakeLoadOneDriveAPI);
    });
  });

  describe('#showPicker', () => {
    it('invokes `window.OneDrive.open` if OneDrive client loaded successfully', () => {
      const callbacks = { success: () => {} };
      const oneDrive = createClient();

      // Emulate the successfully loading
      window.OneDrive = {
        open: sinon.stub(),
      };
      oneDrive.showPicker(callbacks);

      assert.calledOnce(window.OneDrive.open);
      assert.calledWith(
        window.OneDrive.open,
        sinon.match({
          clientId: '12345',
          advanced: { redirectUri: 'https://redirect.uri' },
          ...callbacks,
        })
      );
    });

    it('fails to invoke `window.OneDrive.open` if OneDrive client failed to load', () => {
      const oneDrive = createClient();
      let expectedError;

      // Emulate failure to load the OneDrive client:
      // 1. an unhandled rejection raised in the constructor
      // 2. window.OneDrive is undefined
      try {
        oneDrive.showPicker();
      } catch (error) {
        expectedError = error;
      }

      assert.instanceOf(expectedError, Error); // window.OneDrive is undefined
    });
  });

  describe('#encodeSharingURL', () => {
    it('calls `loadOneDriveAPI`', () => {
      const url = OneDrivePickerClient.encodeSharingURL(
        'https://1drv.ms/b/s!AmH'
      );

      assert.equal(
        url,
        'https://api.onedrive.com/v1.0/shares/u!aHR0cHM6Ly8xZHJ2Lm1zL2IvcyFBbUg/root/content'
      );
    });
  });
});
