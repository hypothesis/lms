/* eslint-disable new-cap */

import { mount } from 'enzyme';

import { act } from 'preact/test-utils';

import mockImportedComponents from '../../../test-util/mock-imported-components';
import { delay, waitFor } from '../../../test-util/wait';
import { Config } from '../../config';
import { PickerCanceledError, PickerPermissionError } from '../../errors';
import ContentSelector, { $imports } from '../ContentSelector';

function interact(wrapper, callback) {
  act(callback);
  wrapper.update();
}

describe('ContentSelector', () => {
  let fakeConfig;
  let FakeGooglePickerClient;
  let FakeOneDrivePickerClient;

  beforeEach(() => {
    FakeGooglePickerClient = sinon.stub().returns({
      showPicker: sinon.stub(),
      enablePublicViewing: sinon.stub(),
    });

    FakeOneDrivePickerClient = sinon.stub().returns({
      showPicker: sinon.stub(),
    });

    fakeConfig = {
      api: { authToken: 'dummy-auth-token' },
      filePicker: {
        blackboard: {
          enabled: true,
          listFiles: {
            authUrl: 'https://lms.anno.co/blackboard/authorize',
            path: 'https://lms.anno.co/api/blackboard/files',
          },
        },
        canvas: {
          enabled: true,
          listFiles: {
            authUrl: 'https://lms.anno.co/canvas/authorize',
            path: 'https://lms.anno.co/api/canvas/files',
          },
        },
        google: {},
        microsoftOneDrive: {
          enabled: true,
          clientId: '12345',
          redirectURI: 'https://myredirect.uri',
        },
        vitalSource: {
          enabled: false,
        },
      },
    };
    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../utils/google-picker-client': {
        GooglePickerClient: FakeGooglePickerClient,
      },
      '../utils/onedrive-picker-client': {
        OneDrivePickerClient: FakeOneDrivePickerClient,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  const renderContentSelector = (props = {}) => {
    const noop = () => {};
    return mount(
      <Config.Provider value={fakeConfig}>
        <ContentSelector onError={noop} onSelectContent={noop} {...props} />
      </Config.Provider>
    );
  };

  const isLoadingIndicatorVisible = wrapper =>
    wrapper.exists('FullScreenSpinner');

  it('renders Canvas file picker button if Canvas file picker enabled', () => {
    fakeConfig.filePicker.canvas.enabled = true;
    const wrapper = renderContentSelector();
    assert.isTrue(
      wrapper.exists('LabeledButton[data-testid="canvas-file-button"]')
    );
  });

  it('does not render Canvas file picker button if Canvas file picker not enabled', () => {
    fakeConfig.filePicker.canvas.enabled = false;
    const wrapper = renderContentSelector();
    assert.isFalse(
      wrapper.exists('LabeledButton[data-testid="canvas-file-button"]')
    );
  });

  it('renders initial form with no dialog visible', () => {
    const wrapper = renderContentSelector();

    assert.isFalse(wrapper.exists('LMSFilePicker'));
    assert.isFalse(wrapper.exists('URLPicker'));
    assert.deepEqual(
      wrapper.find('LabeledButton').map(button => button.prop('data-testid')),
      [
        'url-button',
        'canvas-file-button',
        'blackboard-file-button',
        'onedrive-button',
      ]
    );
  });

  it('shows URL selection dialog when "Enter URL" button is clicked', () => {
    const wrapper = renderContentSelector();

    assert.isFalse(isLoadingIndicatorVisible(wrapper));

    const btn = wrapper.find('LabeledButton[data-testid="url-button"]');
    interact(wrapper, () => {
      btn.props().onClick();
    });

    const urlPicker = wrapper.find('URLPicker');
    assert.isTrue(urlPicker.exists());

    interact(wrapper, () => {
      urlPicker.props().onCancel();
    });
    assert.isFalse(isLoadingIndicatorVisible(wrapper));
  });

  it('supports selecting a URL', () => {
    const onSelectContent = sinon.stub();
    const wrapper = renderContentSelector({
      defaultActiveDialog: 'url',
      onSelectContent,
    });

    const picker = wrapper.find('URLPicker');
    interact(wrapper, () => {
      picker.props().onSelectURL('https://example.com');
    });

    assert.calledWith(onSelectContent, {
      type: 'url',
      url: 'https://example.com',
    });
  });

  describe('LMS file dialog', () => {
    [
      {
        name: 'Canvas',
        buttonTestId: 'canvas-file-button',
        files: () => fakeConfig.filePicker.canvas.listFiles,
      },
      {
        name: 'Blackboard',
        buttonTestId: 'blackboard-file-button',
        files: () => fakeConfig.filePicker.blackboard.listFiles,
      },
    ].forEach(test => {
      it(`shows LMS file dialog when "Select PDF from ${test.name}" is clicked`, () => {
        const wrapper = renderContentSelector();

        const btn = wrapper.find(
          `LabeledButton[data-testid="${test.buttonTestId}"]`
        );
        interact(wrapper, () => {
          btn.props().onClick();
        });

        const filePicker = wrapper.find('LMSFilePicker');
        assert.isTrue(filePicker.exists());
        assert.equal(filePicker.prop('authToken'), fakeConfig.api.authToken);

        assert.equal(filePicker.prop('listFilesApi'), test.files());

        interact(wrapper, () => {
          filePicker.props().onCancel();
        });
      });
    });

    [
      {
        name: 'canvas',
        dialogName: 'canvasFile',
        file: { id: 123 },
        result: {
          type: 'file',
          file: { id: 123 },
        },
        missingFilesHelpLink:
          'https://community.canvaslms.com/t5/Instructor-Guide/How-do-I-upload-a-file-to-a-course/ta-p/618',
      },
      {
        name: 'blackboard',
        dialogName: 'blackboardFile',
        file: { id: 'blackboard://content-resource/123' },
        result: {
          type: 'url',
          url: 'blackboard://content-resource/123',
        },
        missingFilesHelpLink: 'https://web.hypothes.is/help/bb-files',
      },
    ].forEach(test => {
      it(`supports selecting a file from the ${test.name} file dialog`, () => {
        const onSelectContent = sinon.stub();
        const wrapper = renderContentSelector({
          defaultActiveDialog: test.dialogName,
          onSelectContent,
        });

        const picker = wrapper.find('LMSFilePicker');
        interact(wrapper, () => {
          picker.props().onSelectFile(test.file);
        });

        assert.calledWith(onSelectContent, test.result);
      });

      it('passes the appropriate `missingFilesHelpLink` value to `LMSFilePicker`', () => {
        const wrapper = renderContentSelector({
          defaultActiveDialog: test.dialogName,
        });
        assert.equal(
          wrapper.find('LMSFilePicker').prop('missingFilesHelpLink'),
          test.missingFilesHelpLink
        );
      });
    });
  });

  describe('Google picker', () => {
    beforeEach(() => {
      fakeConfig.filePicker.google = {
        clientId: 'goog-client-id',
        developerKey: 'goog-developer-key',
        origin: 'https://test.chalkboard.com',
      };

      const picker = FakeGooglePickerClient();
      picker.showPicker.resolves({
        id: 'doc1',
        name: 'Floops.pdf',
        url: 'https://files.google.com/doc1',
      });
      picker.enablePublicViewing.resolves();

      // Silence errors logged if showing Google Picker fails.
      sinon.stub(console, 'error');
    });

    afterEach(() => {
      console.error.restore();
    });

    function clickGoogleDriveButton(wrapper) {
      const btn = wrapper.find(
        'LabeledButton[data-testid="google-drive-button"]'
      );
      interact(wrapper, () => {
        btn.props().onClick();
      });
    }

    it('initializes Google Picker client when developer key is provided', () => {
      renderContentSelector();
      assert.calledWith(FakeGooglePickerClient, fakeConfig.filePicker.google);
    });

    it('shows "Select PDF from Google Drive" button if developer key is provided', () => {
      const wrapper = renderContentSelector();
      assert.isTrue(
        wrapper.exists('LabeledButton[data-testid="google-drive-button"]')
      );
    });

    it('shows Google Picker when "Select PDF from Google Drive" is clicked', async () => {
      const wrapper = renderContentSelector();
      const picker = FakeGooglePickerClient();

      clickGoogleDriveButton(wrapper);
      await delay(0);

      assert.calledOnce(picker.showPicker);
      assert.calledWith(picker.enablePublicViewing, 'doc1');
    });

    it('submits a Google Drive download URL when a file is selected', async () => {
      const onSelectContent = sinon.stub();
      const wrapper = renderContentSelector({ onSelectContent });

      clickGoogleDriveButton(wrapper);
      await delay(0);

      assert.calledWith(onSelectContent, {
        name: 'Floops.pdf',
        type: 'url',
        url: 'https://files.google.com/doc1',
      });
    });

    it('shows loading indicator while waiting for user to pick file', () => {
      const wrapper = renderContentSelector();
      assert.isFalse(isLoadingIndicatorVisible(wrapper));
      clickGoogleDriveButton(wrapper);
      assert.isTrue(isLoadingIndicatorVisible(wrapper));
    });

    it('shows error message if Google Picker fails to load', async () => {
      const error = new Error('Failed to load');
      FakeGooglePickerClient().showPicker.rejects(error);
      const onError = sinon.stub();
      const wrapper = renderContentSelector({ onError });

      clickGoogleDriveButton(wrapper);
      await delay(0);

      assert.calledWith(onError, {
        description: 'There was a problem choosing a file from Google Drive',
        error,
      });
    });

    it('does not show error message if user cancels picker', async () => {
      FakeGooglePickerClient().showPicker.rejects(new PickerCanceledError());
      const onError = sinon.stub();
      const wrapper = renderContentSelector({ onError });

      clickGoogleDriveButton(wrapper);
      await delay(0);

      assert.notCalled(onError);
    });

    it('hides loading indicator if user cancels picker', async () => {
      FakeGooglePickerClient().showPicker.rejects(new PickerCanceledError());
      const wrapper = renderContentSelector();

      clickGoogleDriveButton(wrapper);
      await delay(0);

      wrapper.setProps({}); // Force re-render.
      assert.isFalse(isLoadingIndicatorVisible(wrapper));
    });
  });

  describe('OneDrive picker', () => {
    let picker;

    function clickOneDriveButton(wrapper) {
      const btn = wrapper.find('LabeledButton[data-testid="onedrive-button"]');
      interact(wrapper, () => {
        btn.props().onClick();
      });
    }

    beforeEach(() => {
      picker = FakeOneDrivePickerClient();
      // Silence errors logged if showing OneDrive Picker fails.
      sinon.stub(console, 'error');
    });

    afterEach(() => {
      console.error.restore();
    });

    it('skips initialization of OneDrive Picker client if parameters not provided', () => {
      FakeOneDrivePickerClient.resetHistory();
      fakeConfig.filePicker.microsoftOneDrive = {
        enabled: true, // clientId and redirectURI are undefined
      };
      renderContentSelector();

      assert.notCalled(FakeOneDrivePickerClient);
    });

    it("doesn't show the OneDrive button if option is disabled", () => {
      fakeConfig.filePicker.microsoftOneDrive.enabled = false; // clientId and redirectURI are defined
      const wrapper = renderContentSelector();

      assert.isFalse(
        wrapper.exists('LabeledButton[data-testid="onedrive-button"]')
      );
    });

    it('initializes OneDrive Picker client if parameters are provided', () => {
      renderContentSelector();

      const { clientId, redirectURI } = fakeConfig.filePicker.microsoftOneDrive;
      assert.calledWith(FakeOneDrivePickerClient, { clientId, redirectURI });
    });

    it('shows the OneDrive button if option is enabled', () => {
      const wrapper = renderContentSelector();

      assert.isTrue(
        wrapper.exists('LabeledButton[data-testid="onedrive-button"]')
      );
    });

    it('shows OneDrive Picker when button is clicked', async () => {
      const wrapper = renderContentSelector();
      picker.showPicker.rejects(new PickerCanceledError());

      clickOneDriveButton(wrapper);
      await delay(0);

      assert.calledOnce(picker.showPicker);
    });

    it('shows loading indicator while waiting for user to pick file', () => {
      const wrapper = renderContentSelector();
      assert.isFalse(isLoadingIndicatorVisible(wrapper));

      clickOneDriveButton(wrapper);

      assert.isTrue(isLoadingIndicatorVisible(wrapper));
    });

    it('submits a OneDrive sharing URL when a file is selected', async () => {
      const onSelectContent = sinon.stub();
      const wrapper = renderContentSelector({ onSelectContent });
      // Emulate the selection of a file in the picker.
      picker.showPicker.resolves({
        name: 'Floops.pdf',
        url: 'https://api.onedrive.com/v1.0/shares/u!https://1drv.ms/b/s!AmH',
      });

      clickOneDriveButton(wrapper);
      await delay(0);

      assert.calledWith(onSelectContent, {
        name: 'Floops.pdf',
        type: 'url',
        url: 'https://api.onedrive.com/v1.0/shares/u!https://1drv.ms/b/s!AmH',
      });
    });

    it('hides loading indicator if user cancels picker', async () => {
      const onError = sinon.stub();
      const wrapper = renderContentSelector({ onError });
      // Emulate the cancellation of the picker.
      picker.showPicker.rejects(new PickerCanceledError());

      clickOneDriveButton(wrapper);
      await waitFor(() => {
        wrapper.update();
        return isLoadingIndicatorVisible(wrapper) === false;
      });

      assert.notCalled(onError);
    });

    it('shows error message if OneDrive Picker raises a permission error', async () => {
      const error = new PickerPermissionError();
      const onError = sinon.stub();
      const wrapper = renderContentSelector({ onError });
      // Emulate a permission error of the picker.
      picker.showPicker.rejects(error);

      clickOneDriveButton(wrapper);
      await delay(0);

      assert.calledWith(onError, {
        description: 'There was a problem choosing a file from OneDrive',
        error,
        children: sinon.match.object,
      });
    });

    it('shows error message if OneDrive Picker errors', async () => {
      const error = new Error('Some failure');
      const onError = sinon.stub();
      const wrapper = renderContentSelector({ onError });
      // Emulate a generic failure in the picker
      picker.showPicker.rejects(error);

      clickOneDriveButton(wrapper);
      await delay(0);

      assert.calledWith(onError, {
        description: 'There was a problem choosing a file from OneDrive',
        error,
      });
      assert.calledWith(console.error, error);
    });
  });

  it('renders VitalSource picker button if enabled', () => {
    fakeConfig.filePicker.vitalSource.enabled = true;
    const wrapper = renderContentSelector();
    assert.isTrue(
      wrapper.exists('LabeledButton[data-testid="vitalsource-button"]')
    );
  });

  it('shows VitalSource book picker when VitalSource button is clicked', () => {
    fakeConfig.filePicker.vitalSource.enabled = true;
    const onSelectContent = sinon.stub();
    const wrapper = renderContentSelector({ onSelectContent });

    const button = wrapper.find(
      'LabeledButton[data-testid="vitalsource-button"]'
    );
    interact(wrapper, () => {
      button.props().onClick();
    });

    assert.isTrue(wrapper.exists('BookPicker'));
  });

  it('submits VitalSource chapter URL', () => {
    const onSelectContent = sinon.stub();
    const wrapper = renderContentSelector({
      defaultActiveDialog: 'vitalSourceBook',
      onSelectContent,
    });

    const picker = wrapper.find('BookPicker');
    interact(wrapper, () => {
      picker
        .props()
        .onSelectBook(
          { id: 'test-book' },
          { url: 'vitalsource://book/BOOK_ID/cfi/CFI' }
        );
    });

    assert.calledWith(onSelectContent, {
      type: 'url',
      url: 'vitalsource://book/BOOK_ID/cfi/CFI',
    });
  });
});
