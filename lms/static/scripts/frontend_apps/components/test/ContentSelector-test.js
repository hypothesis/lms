/* eslint-disable new-cap */

import { mount } from 'enzyme';
import { createElement } from 'preact';
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
        canvas: {
          enabled: true,
          listFiles: {
            authUrl: 'https://lms.anno.co/authorize',
            path: 'https://lms.anno.co/api/files',
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

  it('renders Canvas file picker button if Canvas file picker enabled', () => {
    fakeConfig.filePicker.canvas.enabled = true;
    const wrapper = renderContentSelector();
    assert.isTrue(
      wrapper.exists('LabeledButton[data-testid="lms-file-button"]')
    );
  });

  it('does not render Canvas file picker button if Canvas file picker not enabled', () => {
    fakeConfig.filePicker.canvas.enabled = false;
    const wrapper = renderContentSelector();
    assert.isFalse(
      wrapper.exists('LabeledButton[data-testid="lms-file-button"]')
    );
  });

  it('renders initial form with no dialog visible', () => {
    const wrapper = renderContentSelector();

    assert.isFalse(wrapper.exists('LMSFilePicker'));
    assert.isFalse(wrapper.exists('URLPicker'));
    assert.equal(wrapper.find('LabeledButton').length, 2);
  });

  it('shows URL selection dialog when "Enter URL" button is clicked', () => {
    const wrapper = renderContentSelector();

    assert.isFalse(wrapper.find('.ContentSelector__loading-backdrop').exists());

    const btn = wrapper.find('LabeledButton[data-testid="url-button"]');
    interact(wrapper, () => {
      btn.props().onClick();
    });

    const urlPicker = wrapper.find('URLPicker');
    assert.isTrue(urlPicker.exists());
    assert.isTrue(wrapper.find('.ContentSelector__loading-backdrop').exists());

    interact(wrapper, () => {
      urlPicker.props().onCancel();
    });
    assert.isFalse(wrapper.find('.ContentSelector__loading-backdrop').exists());
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

  it('shows LMS file dialog when "Select PDF from Canvas" is clicked', () => {
    const wrapper = renderContentSelector();

    assert.isFalse(wrapper.find('.ContentSelector__loading-backdrop').exists());

    const btn = wrapper.find('LabeledButton[data-testid="lms-file-button"]');
    interact(wrapper, () => {
      btn.props().onClick();
    });

    assert.isTrue(wrapper.find('.ContentSelector__loading-backdrop').exists());

    const filePicker = wrapper.find('LMSFilePicker');
    assert.isTrue(filePicker.exists());
    assert.equal(filePicker.prop('authToken'), fakeConfig.api.authToken);
    assert.equal(
      filePicker.prop('listFilesApi'),
      fakeConfig.filePicker.canvas.listFiles
    );

    interact(wrapper, () => {
      filePicker.props().onCancel();
    });
    assert.isFalse(wrapper.find('.ContentSelector__loading-backdrop').exists());
  });

  it('supports selecting an LMS file', () => {
    const onSelectContent = sinon.stub();
    const wrapper = renderContentSelector({
      defaultActiveDialog: 'lmsFile',
      onSelectContent,
    });
    const file = { id: 123 };

    const picker = wrapper.find('LMSFilePicker');
    interact(wrapper, () => {
      picker.props().onSelectFile(file);
    });

    assert.calledWith(onSelectContent, {
      type: 'file',
      file,
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
      assert.isFalse(wrapper.exists('Spinner'));
      clickGoogleDriveButton(wrapper);
      assert.isTrue(wrapper.exists('Spinner'));
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
      assert.isFalse(wrapper.exists('Spinner'));
    });
  });

  it('renders VitalSource picker button if enabled', () => {
    fakeConfig.filePicker.vitalSource.enabled = true;
    const wrapper = renderContentSelector();
    assert.isTrue(
      wrapper.exists('LabeledButton[data-testid="vitalsource-button"]')
    );
  });

  it('submits hard-coded book and chapter when VitalSource button is selected', () => {
    fakeConfig.filePicker.vitalSource.enabled = true;
    const onSelectContent = sinon.stub();
    const wrapper = renderContentSelector({ onSelectContent });

    const button = wrapper.find(
      'LabeledButton[data-testid="vitalsource-button"]'
    );
    interact(wrapper, () => {
      button.props().onClick();
    });

    assert.calledWith(onSelectContent, {
      type: 'vitalsource',
      bookID: 'BOOKSHELF-TUTORIAL',
      cfi: '/6/8[;vnd.vst.idref=vst-70a6f9d3-0932-45ba-a583-6060eab3e536]',
    });
  });
});
