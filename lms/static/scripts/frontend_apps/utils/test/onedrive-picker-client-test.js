import { delay } from '../../../test-util/wait';
import { PickerCanceledError } from '../../errors';
import { OneDrivePickerClient, $imports } from '../onedrive-picker-client';

describe('OneDrivePickerClient', () => {
  let fakeLoadOneDriveAPI;
  let fakeOneDrive;
  const clientOptions = {
    clientId: '12345',
    redirectURI: 'https://redirect.uri',
  };

  function createClient({ clientId, redirectURI } = clientOptions) {
    return new OneDrivePickerClient({ clientId, redirectURI });
  }

  beforeEach(() => {
    fakeLoadOneDriveAPI = sinon.stub();
    fakeOneDrive = {
      open: sinon.stub(),
    };

    $imports.$mock({
      './onedrive-api-client': {
        loadOneDriveAPI: fakeLoadOneDriveAPI,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  describe('#showPicker', () => {
    it('fails to invoke `oneDriveAPI.open` method if OneDrive client failed to load', async () => {
      const errorLoading = new Error('Failed to load OneDrive API');
      fakeLoadOneDriveAPI.rejects(errorLoading);
      const oneDrive = createClient();
      let expectedError;

      try {
        await oneDrive.showPicker();
      } catch (error) {
        expectedError = error;
      }

      assert.equal(expectedError, errorLoading);
    });

    it('resolves with a URL when a file is selected', async () => {
      fakeLoadOneDriveAPI.resolves(fakeOneDrive);
      const oneDrive = createClient();

      // Emulate the user selecting a file.
      const pickResult = oneDrive.showPicker();
      await delay(0);
      const { success } = fakeOneDrive.open.getCall(0).args[0];
      success({
        value: [
          { permissions: [{ link: { webUrl: 'https://1drv.ms/b/s!AmH' } }] },
        ],
      });
      const { url } = await pickResult;

      const { clientId, redirectURI: redirectUri } = clientOptions;
      assert.calledWith(
        fakeOneDrive.open,
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
      fakeLoadOneDriveAPI.resolves(fakeOneDrive);
      const oneDrive = createClient();

      // Emulate the user cancelling the picker.
      const pickResult = oneDrive.showPicker();
      await delay(0);
      const { cancel } = fakeOneDrive.open.getCall(0).args[0];
      cancel();
      try {
        await pickResult;
      } catch (error) {
        expectedError = error;
      }

      assert.instanceOf(expectedError, PickerCanceledError);
    });

    it('rejects with an error if the picker has other problems', async () => {
      fakeLoadOneDriveAPI.resolves(fakeOneDrive);
      const oneDriveError = new Error('OneDrive picker internal error');
      const oneDrive = createClient();
      let expectedError;

      // Emulate the picker erroring while the user interacts with it.
      const pickResult = oneDrive.showPicker();
      await delay(0);
      const { error } = fakeOneDrive.open.getCall(0).args[0];
      error(oneDriveError);
      try {
        await pickResult;
      } catch (error) {
        expectedError = error;
      }

      assert.equal(expectedError, oneDriveError);
    });
  });

  describe('.encodeSharingURL', () => {
    [
      {
        sharingURL: 'https://test-account.sharepoint.com/FILE_ID',
        expectedResult:
          'https://test-account.sharepoint.com/FILE_ID?download=1',
        reason: 'Sharepoint, appends query param',
      },
      {
        sharingURL: atob('aHR0cHM6Ly8xZHJ2Lm1zL2IvaQ=='), // https://1drv.ms/b/i
        expectedResult:
          'https://api.onedrive.com/v1.0/shares/u!aHR0cHM6Ly8xZHJ2Lm1zL2IvaQ/root/content',
        reason: 'OneDrive, removing the trailing `=` characters ',
      },
      {
        sharingURL: atob('aHR0cHM6Ly8xZHJ2Lm1zL2Iv++8='), // https://1drv.ms/b/ûï
        expectedResult:
          'https://api.onedrive.com/v1.0/shares/u!aHR0cHM6Ly8xZHJ2Lm1zL2Iv--8/root/content',
        reason: 'OneDrive, removing the `+` characters ',
      },
      {
        sharingURL: atob('aHR0cHM6Ly8xZHJ2Lm1zL2Iva///'), // https://1drv.ms/b/kÿÿ
        expectedResult:
          'https://api.onedrive.com/v1.0/shares/u!aHR0cHM6Ly8xZHJ2Lm1zL2Iva___/root/content',
        reason: 'OneDrive, removing the `/` characters ',
      },
    ].forEach(({ sharingURL, expectedResult, reason }) => {
      it(`creates the download URL for ${reason}`, () => {
        const url = OneDrivePickerClient.downloadURL(sharingURL);

        assert.equal(url, expectedResult);
      });
    });
  });
});
