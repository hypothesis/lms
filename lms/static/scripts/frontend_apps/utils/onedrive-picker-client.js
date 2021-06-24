import { loadOneDriveAPI } from './onedrive-api-client';

export class OneDrivePickerClient {
  constructor({ clientId, redirectURI }) {
    loadOneDriveAPI();

    this._filePickerOptions = {
      clientId: clientId,
      action: 'query',
      multiSelect: false,
      viewType: 'files', //  	The type of item that can be selected.
      advanced: {
        redirectUri: redirectURI,
        filter: '.pdf',
        createLinkParameters: { type: 'view', scope: 'anonymous' },
      },
    };
  }

  async showPicker(success) {
    const callbacks = { success: success };
    window.OneDrive.open({ ...this._filePickerOptions, ...callbacks });
  }
}
