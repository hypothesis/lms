/* eslint-disable new-cap */

import { mount } from 'enzyme';

import { act } from 'preact/test-utils';

import mockImportedComponents from '../../../test-util/mock-imported-components';
import { Config } from '../../config';
import { PickerCanceledError } from '../../utils/google-picker-client';
import ContentSelector, { $imports } from '../ContentSelector';

function interact(wrapper, callback) {
  act(callback);
  wrapper.update();
}

describe('ContentSelector', () => {
  let fakeConfig;
  let FakeGooglePickerClient;

  beforeEach(() => {
    FakeGooglePickerClient = sinon.stub().returns({
      showPicker: sinon.stub(),
      enablePublicViewing: sinon.stub(),
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
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  const renderContentSelector = (props = {}) => {
    const noop = () => {};
    return mount(
      <Config.Provider value={fakeConfig}>
        <ContentSelector
          setErrorInfo={noop}
          onSelectContent={noop}
          {...props}
        />
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
      ['url-button', 'canvas-file-button', 'blackboard-file-button']
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
    assert.isTrue(isLoadingIndicatorVisible(wrapper));

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

        assert.isFalse(isLoadingIndicatorVisible(wrapper));

        const btn = wrapper.find(
          `LabeledButton[data-testid="${test.buttonTestId}"]`
        );
        interact(wrapper, () => {
          btn.props().onClick();
        });

        assert.isTrue(isLoadingIndicatorVisible(wrapper));

        const filePicker = wrapper.find('LMSFilePicker');
        assert.isTrue(filePicker.exists());
        assert.equal(filePicker.prop('authToken'), fakeConfig.api.authToken);

        assert.equal(filePicker.prop('listFilesApi'), test.files());

        interact(wrapper, () => {
          filePicker.props().onCancel();
        });
        assert.isFalse(isLoadingIndicatorVisible(wrapper));
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
        url: 'https://files.google.com/doc1',
      });
      picker.enablePublicViewing.resolves();
      FakeGooglePickerClient.resetHistory();

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
      clickGoogleDriveButton(wrapper);
      const picker = FakeGooglePickerClient();
      assert.called(picker.showPicker);

      const { id } = await picker.showPicker();

      assert.calledWith(picker.enablePublicViewing, id);
    });

    it('submits a Google Drive download URL when a file is selected', async () => {
      let resolveContent;
      const contentPromise = new Promise(resolve => (resolveContent = resolve));
      const onSelectContent = resolveContent;
      const wrapper = renderContentSelector({ onSelectContent });

      clickGoogleDriveButton(wrapper);
      const content = await contentPromise;

      assert.deepEqual(content, {
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
      try {
        await FakeGooglePickerClient().showPicker();
      } catch (e) {
        /* noop */
      }

      assert.calledWith(onError, {
        title: 'There was a problem choosing a file from Google Drive',
        error,
      });
    });

    it('does not show error message if user cancels picker', async () => {
      FakeGooglePickerClient().showPicker.rejects(new PickerCanceledError());
      const onError = sinon.stub();
      const wrapper = renderContentSelector({ onError });

      clickGoogleDriveButton(wrapper);
      try {
        await FakeGooglePickerClient().showPicker();
      } catch (e) {
        /* noop */
      }

      assert.notCalled(onError);
    });

    it('hides loading indicator if user cancels picker', async () => {
      FakeGooglePickerClient().showPicker.rejects(new PickerCanceledError());
      const wrapper = renderContentSelector();

      clickGoogleDriveButton(wrapper);
      try {
        await FakeGooglePickerClient().showPicker();
      } catch (e) {
        /* noop */
      }

      wrapper.setProps({}); // Force re-render.
      assert.isFalse(isLoadingIndicatorVisible(wrapper));
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

  it('submits VitalSource book ID and chapter CFI', () => {
    const onSelectContent = sinon.stub();
    const wrapper = renderContentSelector({
      defaultActiveDialog: 'vitalSourceBook',
      onSelectContent,
    });

    const picker = wrapper.find('BookPicker');
    interact(wrapper, () => {
      picker.props().onSelectBook({ id: 'test-book' }, { cfi: '/1/2' });
    });

    assert.calledWith(onSelectContent, {
      type: 'vitalsource',
      bookID: 'test-book',
      cfi: '/1/2',
    });
  });
});
