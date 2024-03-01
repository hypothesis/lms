/* eslint-disable new-cap */
import {
  delay,
  waitFor,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import { act } from 'preact/test-utils';

import { Config } from '../../config';
import { PickerCanceledError } from '../../errors';
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
          pagesEnabled: true,
          listFiles: {
            authUrl: 'https://lms.anno.co/canvas/authorize',
            path: 'https://lms.anno.co/api/canvas/files',
          },
          listPages: {
            authUrl: 'https://lms.anno.co/canvas/authorize',
            path: 'https://lms.anno.co/api/canvas/pages',
          },
        },
        moodle: {
          enabled: true,
          listFiles: {
            authUrl: 'https://lms.anno.co/moodle/authorize',
            path: 'https://lms.anno.co/api/moodle/files',
          },
        },
        d2l: {
          enabled: true,
          listFiles: {
            authUrl: 'https://lms.anno.co/d2l/authorize',
            path: 'https://lms.anno.co/api/d2l/files',
          },
        },
        google: {},
        jstor: {
          enabled: false,
        },
        microsoftOneDrive: {
          enabled: true,
          clientId: '12345',
          redirectURI: 'https://myredirect.uri',
        },
        vitalSource: {
          enabled: false,
        },
        youtube: {
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
      </Config.Provider>,
    );
  };

  const isLoadingIndicatorVisible = wrapper => wrapper.exists('SpinnerOverlay');

  it('renders Canvas file picker button if Canvas file picker enabled', () => {
    fakeConfig.filePicker.canvas.enabled = true;
    const wrapper = renderContentSelector();
    assert.isTrue(wrapper.exists('Button[data-testid="canvas-file-button"]'));
  });

  it('does not render Canvas file picker button if Canvas file picker not enabled', () => {
    fakeConfig.filePicker.canvas.enabled = false;
    const wrapper = renderContentSelector();
    assert.isFalse(wrapper.exists('Button[data-testid="canvas-file-button"]'));
  });

  it('renders initial form with no dialog visible', () => {
    const wrapper = renderContentSelector();

    assert.isFalse(wrapper.exists('LMSFilePicker'));
    assert.isFalse(wrapper.exists('URLPicker'));
    assert.deepEqual(
      wrapper.find('Button').map(button => button.prop('data-testid')),
      [
        'url-button',
        'canvas-file-button',
        'canvas-page-button',
        'blackboard-file-button',
        'd2l-file-button',
        'moodle-file-button',
        'onedrive-button',
      ],
    );
  });

  it('shows URL selection dialog when "Enter URL" button is clicked', () => {
    const wrapper = renderContentSelector();

    assert.isFalse(isLoadingIndicatorVisible(wrapper));

    const btn = wrapper.find('Button[data-testid="url-button"]');
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

  describe('`initialContent` prop', () => {
    [
      'http://example.com/1234',
      'https://arxiv.org/pdf/1234.pdf',
      'https://foobar.com/a%3Cb',
      'HTTPS://EXAMPLE.COM/4567',
    ].forEach(url => {
      it('pre-fills URL input if `initialContent` is an HTTP URL', () => {
        const wrapper = renderContentSelector({
          defaultActiveDialog: 'url',
          initialContent: { type: 'url', url },
        });
        assert.equal(wrapper.find('URLPicker').prop('defaultURL'), url);
      });
    });

    it('does not open a dialog when `initialContent` is specified', () => {
      const wrapper = renderContentSelector({
        initialContent: { type: 'url', url: 'https://example.com' },
      });
      assert.isFalse(wrapper.exists('URLPicker'));
    });

    ['jstor://1234', 'unknown:foobar'].forEach(url => {
      it('does not pre-fill URL input if `initialContent` is a non-HTTP URL', () => {
        const wrapper = renderContentSelector({
          defaultActiveDialog: 'url',
          initialContent: { type: 'url', url },
        });
        assert.isUndefined(wrapper.find('URLPicker').prop('defaultURL'));
      });
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
      {
        name: 'D2L',
        buttonTestId: 'd2l-file-button',
        files: () => fakeConfig.filePicker.d2l.listFiles,
      },
      {
        name: 'Moodle',
        buttonTestId: 'moodle-file-button',
        files: () => fakeConfig.filePicker.moodle.listFiles,
      },
    ].forEach(test => {
      it(`shows LMS file dialog when "${test.name} file" is clicked`, () => {
        const wrapper = renderContentSelector();

        const btn = wrapper.find(`Button[data-testid="${test.buttonTestId}"]`);
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
      {
        name: 'moodle',
        dialogName: 'moodleFile',
        file: { id: 'moodle://file/FILE' },
        result: {
          type: 'url',
          url: 'moodle://file/FILE',
        },
        missingFilesHelpLink: 'https://web.hypothes.is/help/',
      },

      {
        name: 'd2l',
        dialogName: 'd2lFile',
        file: { id: 'd2l://file/course/123/file_id/456' },
        result: {
          type: 'url',
          url: 'd2l://file/course/123/file_id/456',
        },
        missingFilesHelpLink:
          'https://web.hypothes.is/help/using-hypothesis-with-d2l-course-content-files/',
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
          test.missingFilesHelpLink,
        );
      });
    });
  });

  describe('LMS page dialog', () => {
    it('shows LMS file dialog when "Canvas page" is clicked', () => {
      const wrapper = renderContentSelector();

      const btn = wrapper.find(`Button[data-testid="canvas-page-button"]`);
      interact(wrapper, () => {
        btn.props().onClick();
      });

      const pagePicker = wrapper.find('LMSFilePicker');
      assert.isTrue(pagePicker.exists());
      assert.equal(pagePicker.prop('authToken'), fakeConfig.api.authToken);

      assert.equal(
        pagePicker.prop('listFilesApi'),
        fakeConfig.filePicker.canvas.listPages,
      );

      interact(wrapper, () => {
        pagePicker.props().onCancel();
      });
    });

    it('supports selecting a page from the page dialog', () => {
      const onSelectContent = sinon.stub();
      const wrapper = renderContentSelector({
        defaultActiveDialog: 'canvasPage',
        onSelectContent,
      });

      const picker = wrapper.find('LMSFilePicker');
      interact(wrapper, () => {
        picker.props().onSelectFile({ id: 123, display_name: 'Page title' });
      });

      assert.calledWith(onSelectContent, {
        type: 'url',
        url: 123,
        name: 'Canvas page: Page title',
      });
    });
  });

  describe('Google picker', () => {
    beforeEach(() => {
      fakeConfig.filePicker.google = {
        enabled: true,
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
      const btn = wrapper.find('Button[data-testid="google-drive-button"]');
      interact(wrapper, () => {
        btn.props().onClick();
      });
    }
    it("doesn't show the Google Drive button if option is disabled", () => {
      fakeConfig.filePicker.google.enabled = false;
      const wrapper = renderContentSelector();

      assert.isFalse(
        wrapper.exists('Button[data-testid="google-drive-button"]'),
      );
    });

    it('initializes Google Picker client when developer key is provided', () => {
      const { developerKey, clientId, origin } = fakeConfig.filePicker.google;
      renderContentSelector();
      assert.calledWith(FakeGooglePickerClient, {
        developerKey,
        clientId,
        origin,
      });
    });

    it('shows "Select PDF from Google Drive" button if developer key is provided', () => {
      const wrapper = renderContentSelector();
      assert.isTrue(
        wrapper.exists('Button[data-testid="google-drive-button"]'),
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
        message: 'There was a problem choosing a file from Google Drive',
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
      const btn = wrapper.find('Button[data-testid="onedrive-button"]');
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

      assert.isFalse(wrapper.exists('Button[data-testid="onedrive-button"]'));
    });

    it('initializes OneDrive Picker client if parameters are provided', () => {
      renderContentSelector();

      const { clientId, redirectURI } = fakeConfig.filePicker.microsoftOneDrive;
      assert.calledWith(FakeOneDrivePickerClient, { clientId, redirectURI });
    });

    it('shows the OneDrive button if option is enabled', () => {
      const wrapper = renderContentSelector();

      assert.isTrue(wrapper.exists('Button[data-testid="onedrive-button"]'));
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

    it('shows error message if OneDrive Picker errors', async () => {
      const error = new Error('Some failure');
      const onError = sinon.stub();
      const wrapper = renderContentSelector({ onError });
      // Emulate a failure in the picker
      picker.showPicker.rejects(error);

      clickOneDriveButton(wrapper);
      await delay(0);

      assert.calledWith(onError, {
        message: 'There was a problem choosing a file from OneDrive',
        error,
      });
      assert.calledWith(console.error, error);
    });
  });

  describe('VitalSource picker', () => {
    it('renders VitalSource picker button if enabled', () => {
      fakeConfig.filePicker.vitalSource.enabled = true;
      const wrapper = renderContentSelector();
      assert.isTrue(wrapper.exists('Button[data-testid="vitalsource-button"]'));
    });

    it('shows VitalSource book picker when VitalSource button is clicked', () => {
      fakeConfig.filePicker.vitalSource.enabled = true;
      const onSelectContent = sinon.stub();
      const wrapper = renderContentSelector({ onSelectContent });

      const button = wrapper.find('Button[data-testid="vitalsource-button"]');
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
        picker.props().onSelectBook(
          {
            book: { id: 'test-book' },
            content: {
              type: 'toc',
              start: {
                cfi: 'CFI',
                // ... other fields omitted.
              },
            },
          },
          'vitalsource://book/BOOK_ID/cfi/CFI',
        );
      });

      assert.calledWith(onSelectContent, {
        type: 'url',
        url: 'vitalsource://book/BOOK_ID/cfi/CFI',
      });
    });
  });

  describe('JSTOR picker', () => {
    it('renders JSTOR picker button if enabled', () => {
      fakeConfig.filePicker.jstor.enabled = true;
      const wrapper = renderContentSelector();
      assert.isTrue(wrapper.exists('Button[data-testid="jstor-button"]'));
    });

    it('shows JSTOR picker when JSTOR button is clicked', () => {
      fakeConfig.filePicker.jstor.enabled = true;
      const onSelectContent = sinon.stub();
      const wrapper = renderContentSelector({ onSelectContent });

      const button = wrapper.find('Button[data-testid="jstor-button"]');
      interact(wrapper, () => {
        button.props().onClick();
      });

      assert.isTrue(wrapper.exists('JSTORPicker'));
    });

    it('pre-fills article selection if `initialContent` specifies JSTOR content', () => {
      const wrapper = renderContentSelector({
        initialContent: { type: 'url', url: 'jstor://10.1234/5678' },
        defaultActiveDialog: 'jstor',
      });
      assert.equal(
        wrapper.find('JSTORPicker').prop('defaultArticle'),
        '10.1234/5678',
      );
    });

    it('submits JSTOR URL', () => {
      const onSelectContent = sinon.stub();
      const wrapper = renderContentSelector({
        defaultActiveDialog: 'jstor',
        onSelectContent,
      });

      const picker = wrapper.find('JSTORPicker');
      interact(wrapper, () => {
        picker.props().onSelectURL('jstor://1234');
      });

      assert.calledWith(onSelectContent, {
        type: 'url',
        url: 'jstor://1234',
      });
    });
  });

  describe('YouTube picker', () => {
    const getYouTubePicker = wrapper => wrapper.find('YouTubePicker');

    beforeEach(() => {
      fakeConfig.filePicker.youtube.enabled = true;
    });

    it('renders YouTube picker button if enabled', () => {
      const wrapper = renderContentSelector();
      assert.isTrue(wrapper.exists('Button[data-testid="youtube-button"]'));
    });

    it('shows YouTube picker when YouTube button is clicked', () => {
      const onSelectContent = sinon.stub();
      const wrapper = renderContentSelector({ onSelectContent });

      const button = wrapper.find('Button[data-testid="youtube-button"]');
      interact(wrapper, () => {
        button.props().onClick();
      });

      assert.isTrue(wrapper.exists('YouTubePicker'));
    });

    it('supports selecting a URL', () => {
      const onSelectContent = sinon.stub();
      const wrapper = renderContentSelector({
        defaultActiveDialog: 'youtube',
        onSelectContent,
      });

      const picker = getYouTubePicker(wrapper);
      interact(wrapper, () => {
        picker
          .props()
          .onSelectURL(
            'https://youtu.be/EU6TDnV5osM',
            'The video title (channel)',
          );
      });

      assert.calledWith(onSelectContent, {
        type: 'url',
        url: 'https://youtu.be/EU6TDnV5osM',
        name: 'YouTube: The video title (channel)',
      });
    });

    [
      'https://youtu.be/EU6TDnV5osM',
      'https://www.youtube.com/watch?v=123',
      'https://www.youtube.com/shorts/shortId',
    ].forEach(url => {
      it('sets default value when it is a YouTube URL', () => {
        const wrapper = renderContentSelector({
          defaultActiveDialog: 'youtube',
          initialContent: { type: 'url', url },
        });
        assert.equal(getYouTubePicker(wrapper).prop('defaultURL'), url);
      });
    });

    it('does not set default value when it is not a YouTube URL', () => {
      const wrapper = renderContentSelector({
        defaultActiveDialog: 'youtube',
        initialContent: { type: 'url', url: 'http://example.com/1234' },
      });
      assert.isUndefined(getYouTubePicker(wrapper).prop('defaultURL'));
    });
  });
});
