import { PickerCanceledError } from '../google-picker-client';
import { OneDrivePickerClient, $imports } from '../onedrive-picker-client';

describe('OneDrivePickerClient', () => {
  let fakeLoadOneDriveAPI;
  const clientOptions = {
    clientId: '12345',
    redirectURI: 'https://redirect.uri',
  };

  function createClient({ clientId, redirectURI } = clientOptions) {
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
    it('fails to invoke `window.OneDrive.open` if OneDrive client failed to load', async () => {
      const oneDrive = createClient();
      let expectedError;

      // Emulate failure to load the OneDrive client:
      // 1. an unhandled rejection raised in the constructor
      // 2. window.OneDrive is undefined
      try {
        await oneDrive.showPicker();
      } catch (error) {
        expectedError = error;
      }

      assert.instanceOf(expectedError, Error); // window.OneDrive is undefined
    });

    it('resolves with a file object when a file is selected', async () => {
      const oneDrive = createClient();

      // Emulates the successful loading of the OneDrive client and the user
      // selecting a file.
      window.OneDrive = {
        open: sinon.stub(),
      };
      const onSuccess = oneDrive.showPicker();
      const { success } = window.OneDrive.open.getCall(0).args[0];
      success({
        value: [
          { permissions: [{ link: { webUrl: 'https://1drv.ms/b/s!AmH' } }] },
        ],
      });
      const { url } = await onSuccess;

      const { clientId, redirectURI: redirectUri } = clientOptions;
      assert.calledWith(
        window.OneDrive.open,
        sinon.match({
          clientId,
          advanced: { redirectUri },
        })
      );
      assert.equal(
        url,
        'https://api.onedrive.com/v1.0/shares/u!aHR0cHM6Ly8xZHJ2Lm1zL2IvcyFBbUg/root/content'
      );
    });

    it('rejects with a `PickerCancelledError` if the user cancels the picker', async () => {
      let expectedError;
      const oneDrive = createClient();

      // Emulates the successful loading of the OneDrive client and the user
      // cancelling the picker.
      window.OneDrive = {
        open: sinon.stub(),
      };
      const onCancel = oneDrive.showPicker();
      const { cancel } = window.OneDrive.open.getCall(0).args[0];
      cancel();
      try {
        await onCancel;
      } catch (error) {
        expectedError = error;
      }

      assert.instanceOf(expectedError, PickerCanceledError);
    });

    it('rejects with an error if the picker has other problems', async () => {
      const oneDrive = createClient();
      const oneDriveError = new Error('OneDrive picker internal error');
      let expectedError;

      // Emulate the successful loading of the OneDrive client and the picker
      // erroring while the user interacting with it.
      window.OneDrive = {
        open: sinon.stub(),
      };
      const onError = oneDrive.showPicker();
      const { error } = window.OneDrive.open.getCall(0).args[0];
      error(oneDriveError);
      try {
        await onError;
      } catch (error) {
        expectedError = error;
      }

      assert.equal(oneDriveError, expectedError);
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
