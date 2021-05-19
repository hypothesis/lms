/* eslint-disable new-cap */

import { createElement } from 'preact';
import { act } from 'preact/test-utils';
import { mount } from 'enzyme';

import { Config } from '../../config';
import { PickerCanceledError } from '../../utils/google-picker-client';
import FilePickerApp, { $imports } from '../FilePickerApp';
import { checkAccessibility } from '../../../test-util/accessibility';
import mockImportedComponents from '../../../test-util/mock-imported-components';

function interact(wrapper, callback) {
  act(callback);
  wrapper.update();
}

describe('FilePickerApp', () => {
  let container;
  let fakeConfig;
  let FakeGooglePickerClient;

  const renderFilePicker = (props = {}) => {
    const preventFormSubmission = e => e.preventDefault();
    return mount(
      <Config.Provider value={fakeConfig}>
        <FilePickerApp onSubmit={preventFormSubmission} {...props} />
      </Config.Provider>,
      {
        attachTo: container,
      }
    );
  };

  beforeEach(() => {
    fakeConfig = {
      api: { authToken: 'dummy-auth-token' },
      filePicker: {
        formAction: 'https://www.shinylms.com/',
        formFields: { hidden_field: 'hidden_value' },
        canvas: {
          enabled: true,
          ltiLaunchUrl: 'https://lms.anno.co/lti_launch',
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

    container = document.createElement('div');
    document.body.appendChild(container);

    FakeGooglePickerClient = sinon.stub().returns({
      showPicker: sinon.stub(),
      enablePublicViewing: sinon.stub(),
    });

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../utils/google-picker-client': {
        GooglePickerClient: FakeGooglePickerClient,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
    container.remove();
  });

  /**
   * Check that the expected hidden form fields were set.
   */
  function checkFormFields(wrapper, expectedContent) {
    const formFields = wrapper.find('FilePickerFormFields');
    assert.deepEqual(formFields.props(), {
      children: [],
      content: expectedContent,
      formFields: fakeConfig.filePicker.formFields,
      ltiLaunchURL: fakeConfig.filePicker.canvas.ltiLaunchUrl,
    });
  }

  it('renders form with correct action', () => {
    const wrapper = renderFilePicker();
    const form = wrapper.find('form');
    assert.equal(form.prop('action'), 'https://www.shinylms.com/');
  });

  it('renders buttons to choose assignment source', () => {
    const wrapper = renderFilePicker();
    assert.equal(wrapper.find('LabeledButton').length, 2);
  });

  it('renders Canvas file picker button if Canvas file picker enabled', () => {
    fakeConfig.filePicker.canvas.enabled = true;
    const wrapper = renderFilePicker();
    assert.isTrue(wrapper.exists('LabeledButton[data-test="pdf-button"]'));
  });

  it('does not render Canvas file picker button if Canvas file picker not enabled', () => {
    fakeConfig.filePicker.canvas.enabled = false;
    const wrapper = renderFilePicker();
    assert.isFalse(wrapper.exists('LabeledButton[data-test="pdf-button"]'));
  });

  it('renders initial form with no dialog visible', () => {
    const wrapper = renderFilePicker();

    assert.isFalse(wrapper.exists('LMSFilePicker'));
    assert.isFalse(wrapper.exists('URLPicker'));
    assert.equal(wrapper.find('LabeledButton').length, 2);
  });

  it('shows URL selection dialog when "Enter URL" button is clicked', () => {
    const wrapper = renderFilePicker();

    assert.isFalse(wrapper.find('.FilePickerApp__loading-backdrop').exists());

    const btn = wrapper.find('LabeledButton[data-test="url-button"]');
    interact(wrapper, () => {
      btn.props().onClick();
    });

    const urlPicker = wrapper.find('URLPicker');
    assert.isTrue(urlPicker.exists());
    assert.isTrue(wrapper.find('.FilePickerApp__loading-backdrop').exists());

    interact(wrapper, () => {
      urlPicker.props().onCancel();
    });
    assert.isFalse(wrapper.find('.FilePickerApp__loading-backdrop').exists());
  });

  it('submits a URL when a URL is selected', () => {
    const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
    const wrapper = renderFilePicker({ defaultActiveDialog: 'url', onSubmit });

    const picker = wrapper.find('URLPicker');
    interact(wrapper, () => {
      picker.props().onSelectURL('https://example.com');
    });

    assert.called(onSubmit);
    checkFormFields(wrapper, {
      type: 'url',
      url: 'https://example.com',
    });
  });

  it('shows LMS file dialog when "Select PDF from Canvas" is clicked', () => {
    const wrapper = renderFilePicker();

    assert.isFalse(wrapper.find('.FilePickerApp__loading-backdrop').exists());

    const btn = wrapper.find('LabeledButton[data-test="pdf-button"]');
    interact(wrapper, () => {
      btn.props().onClick();
    });

    assert.isTrue(wrapper.find('.FilePickerApp__loading-backdrop').exists());

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
    assert.isFalse(wrapper.find('.FilePickerApp__loading-backdrop').exists());
  });

  it('submits an LMS file when an LMS file is selected', () => {
    const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
    const wrapper = renderFilePicker({ defaultActiveDialog: 'lms', onSubmit });
    const file = { id: 123 };

    const picker = wrapper.find('LMSFilePicker');
    interact(wrapper, () => {
      picker.props().onSelectFile(file);
    });

    assert.called(onSubmit);
    checkFormFields(wrapper, {
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
      const btn = wrapper.find('LabeledButton[data-test="drive-button"]');
      interact(wrapper, () => {
        btn.props().onClick();
      });
    }

    it('initializes Google Picker client when developer key is provided', () => {
      renderFilePicker();
      assert.calledWith(FakeGooglePickerClient, fakeConfig.filePicker.google);
    });

    it('shows "Select PDF from Google Drive" button if developer key is provided', () => {
      const wrapper = renderFilePicker();
      assert.isTrue(wrapper.exists('LabeledButton[data-test="pdf-button"]'));
    });

    it('shows Google Picker when "Select PDF from Google Drive" is clicked', async () => {
      const wrapper = renderFilePicker();
      clickGoogleDriveButton(wrapper);
      const picker = FakeGooglePickerClient();
      assert.called(picker.showPicker);

      const { id } = await picker.showPicker();

      assert.calledWith(picker.enablePublicViewing, id);
    });

    it('submits a Google Drive download URL when a file is selected', async () => {
      let resolveSubmitted;
      const submitted = new Promise(resolve => (resolveSubmitted = resolve));
      const onSubmit = e => {
        e.preventDefault();
        resolveSubmitted();
      };
      const wrapper = renderFilePicker({ onSubmit });

      clickGoogleDriveButton(wrapper);
      await submitted;

      wrapper.update();
      checkFormFields(wrapper, {
        type: 'url',
        url: 'https://files.google.com/doc1',
      });
    });

    it('shows loading indicator while waiting for user to pick file', () => {
      const wrapper = renderFilePicker();
      assert.isFalse(wrapper.exists('Spinner'));
      clickGoogleDriveButton(wrapper);
      assert.isTrue(wrapper.exists('Spinner'));
    });

    it('shows error message if Google Picker fails to load', async () => {
      const err = new Error('Failed to load');
      FakeGooglePickerClient().showPicker.rejects(err);
      const wrapper = renderFilePicker();

      clickGoogleDriveButton(wrapper);
      try {
        await FakeGooglePickerClient().showPicker();
      } catch (e) {
        /* noop */
      }

      wrapper.setProps({}); // Force re-render.
      const errDialog = wrapper.find('ErrorDialog');
      assert.equal(errDialog.length, 1);
      assert.equal(errDialog.prop('error'), err);
    });

    it('dismisses error dialog if user clicks close button', async () => {
      const err = new Error('Failed to load');
      FakeGooglePickerClient().showPicker.rejects(err);
      const wrapper = renderFilePicker();

      clickGoogleDriveButton(wrapper);
      try {
        await FakeGooglePickerClient().showPicker();
      } catch (e) {
        /* noop */
      }

      wrapper.setProps({}); // Force re-render.
      const errDialog = wrapper.find('ErrorDialog');
      const onCancel = errDialog.prop('onCancel');
      assert.isFunction(onCancel);
      interact(wrapper, onCancel);
      assert.isFalse(wrapper.exists('ErrorDialog'));
    });

    it('does not show error message if user cancels picker', async () => {
      FakeGooglePickerClient().showPicker.rejects(new PickerCanceledError());
      const wrapper = renderFilePicker();

      clickGoogleDriveButton(wrapper);
      try {
        await FakeGooglePickerClient().showPicker();
      } catch (e) {
        /* noop */
      }

      wrapper.setProps({}); // Force re-render.
      assert.isFalse(wrapper.exists('ErrorDialog'));
    });

    it('hides loading indicator if user cancels picker', async () => {
      FakeGooglePickerClient().showPicker.rejects(new PickerCanceledError());
      const wrapper = renderFilePicker();

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

  describe('VitalSource Book selector', () => {
    it('renders VitalSource picker button if enabled', () => {
      fakeConfig.filePicker.vitalSource.enabled = true;
      const wrapper = renderFilePicker();
      assert.isTrue(
        wrapper.exists('LabeledButton[data-test="vitalsource-button"]')
      );
    });

    it('submits hard-coded book and chapter when VitalSource picker button is selected', () => {
      fakeConfig.filePicker.vitalSource.enabled = true;
      const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
      const wrapper = renderFilePicker({ onSubmit });

      const button = wrapper.find(
        'LabeledButton[data-test="vitalsource-button"]'
      );
      interact(wrapper, () => {
        button.props().onClick();
      });

      assert.called(onSubmit);
      checkFormFields(wrapper, {
        type: 'vitalsource',
        bookID: 'BOOKSHELF-TUTORIAL',
        cfi: '/6/8[;vnd.vst.idref=vst-70a6f9d3-0932-45ba-a583-6060eab3e536]',
      });
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderFilePicker(),
    })
  );
});
