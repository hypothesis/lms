/* eslint-disable new-cap */

import { createElement } from 'preact';
import { act } from 'preact/test-utils';
import { mount } from 'enzyme';

import { Config } from '../../config';
import {
  contentItemForLmsFile,
  contentItemForUrl,
} from '../../utils/content-item';
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

  const getContentItem = wrapper =>
    JSON.parse(wrapper.find('input[name="content_items"]').prop('value'));

  beforeEach(() => {
    fakeConfig = {
      api: {},
      filePicker: {
        formAction: 'https://www.shinylms.com/',
        formFields: { hidden_field: 'hidden_value' },
        canvas: {
          enabled: true,
          ltiLaunchUrl: 'https://lms.anno.co/lti_launch',
        },
        google: {},
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

  it('renders form with correct action and hidden fields', () => {
    const wrapper = renderFilePicker();
    const form = wrapper.find('form');

    assert.equal(form.prop('action'), 'https://www.shinylms.com/');

    Object.keys(fakeConfig.filePicker.formFields).forEach(fieldName => {
      const field = form.find(`input[name="${fieldName}"]`);
      assert.equal(field.length, 1);
      assert.equal(
        field.prop('value'),
        fakeConfig.filePicker.formFields[fieldName]
      );
    });
  });

  it('renders buttons to choose assignment source', () => {
    const wrapper = renderFilePicker();
    assert.equal(wrapper.find('Button').length, 2);
  });

  it('renders Canvas file picker button if Canvas file picker enabled', () => {
    fakeConfig.filePicker.canvas.enabled = true;
    const wrapper = renderFilePicker();
    assert.isTrue(wrapper.exists('Button[label="Select PDF from Canvas"]'));
  });

  it('does not render Canvas file picker button if Canvas file picker not enabled', () => {
    fakeConfig.filePicker.canvas.enabled = false;
    const wrapper = renderFilePicker();
    assert.isFalse(wrapper.exists('Button[label="Select PDF from Canvas"]'));
  });

  it('renders initial form with no dialog visible', () => {
    const wrapper = renderFilePicker();

    assert.isFalse(wrapper.exists('LMSFilePicker'));
    assert.isFalse(wrapper.exists('URLPicker'));
    assert.equal(wrapper.find('Button').length, 2);
  });

  it('shows URL selection dialog when "Enter URL" button is clicked', () => {
    const wrapper = renderFilePicker();

    const btn = wrapper.find('Button[label="Enter URL of web page or PDF"]');
    interact(wrapper, () => {
      btn.props().onClick();
    });

    assert.isTrue(wrapper.exists('URLPicker'));
  });

  it('submits a URL when a URL is selected', () => {
    const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
    const wrapper = renderFilePicker({ defaultActiveDialog: 'url', onSubmit });

    const picker = wrapper.find('URLPicker');
    interact(wrapper, () => {
      picker.props().onSelectURL('https://example.com');
    });

    assert.called(onSubmit);
    assert.deepEqual(
      getContentItem(wrapper),
      contentItemForUrl(
        fakeConfig.filePicker.canvas.ltiLaunchUrl,
        'https://example.com'
      )
    );
  });

  it('shows LMS file dialog when "Select PDF from Canvas" is clicked', () => {
    const wrapper = renderFilePicker();

    const btn = wrapper.find('Button[label="Select PDF from Canvas"]');
    interact(wrapper, () => {
      btn.props().onClick();
    });

    assert.isTrue(wrapper.exists('LMSFilePicker'));
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
    assert.deepEqual(
      getContentItem(wrapper),
      contentItemForLmsFile(fakeConfig.filePicker.canvas.ltiLaunchUrl, file)
    );
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
      const btn = wrapper.find('Button[label="Select PDF from Google Drive"]');
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
      assert.isTrue(
        wrapper.exists('Button[label="Select PDF from Google Drive"]')
      );
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
      assert.deepEqual(
        getContentItem(wrapper),
        contentItemForUrl(
          fakeConfig.filePicker.canvas.ltiLaunchUrl,
          'https://files.google.com/doc1'
        )
      );
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

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderFilePicker(),
    })
  );
});
