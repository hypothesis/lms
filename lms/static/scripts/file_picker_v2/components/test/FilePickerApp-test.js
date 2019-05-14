import { createElement } from 'preact';
import { act } from 'preact/test-utils';
import { mount } from 'enzyme';

import { Config } from '../../config';
import {
  contentItemForLmsFile,
  contentItemForUrl,
} from '../../utils/content-item';
import Button from '../Button';
import FilePickerApp, { $imports } from '../FilePickerApp';

function interact(wrapper, callback) {
  act(callback);
  wrapper.update();
}

describe('FilePickerApp', () => {
  const FakeURLPicker = () => null;
  const FakeLMSFilePicker = () => null;
  const FakeGoogleFilePicker = () => null;

  let fakeConfig;

  const renderFilePicker = (props = {}) => {
    const preventFormSubmission = e => e.preventDefault();
    return mount(
      <Config.Provider value={fakeConfig}>
        <FilePickerApp onSubmit={preventFormSubmission} {...props} />
      </Config.Provider>
    );
  };

  const getContentItem = wrapper =>
    JSON.parse(wrapper.find('input[name="content_items"]').prop('value'));

  beforeEach(() => {
    fakeConfig = {
      formAction: 'https://www.shinylms.com/',
      formFields: { hidden_field: 'hidden_value' },
      lmsName: 'Shiny LMS',
      ltiLaunchUrl: 'https://lms.anno.co/lti_launch',
    };

    // nb. We mock these components manually rather than using Enzyme's
    // shallow rendering because the modern context API doesn't seem to work
    // with shallow rendering yet.
    $imports.$mock({
      './GoogleFilePicker': FakeGoogleFilePicker,
      './LMSFilePicker': FakeLMSFilePicker,
      './URLPicker': FakeURLPicker,
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('renders form with correct action and hidden fields', () => {
    const wrapper = renderFilePicker();
    const form = wrapper.find('form');

    assert.equal(form.prop('action'), 'https://www.shinylms.com/');

    Object.keys(fakeConfig.formFields).forEach(fieldName => {
      const field = form.find(`input[name="${fieldName}"]`);
      assert.equal(field.length, 1);
      assert.equal(field.prop('value'), fakeConfig.formFields[fieldName]);
    });
  });

  it('renders initial form with no dialog visible', () => {
    const wrapper = renderFilePicker();

    assert.isFalse(wrapper.exists(FakeLMSFilePicker));
    assert.isFalse(wrapper.exists(FakeURLPicker));
    assert.isFalse(wrapper.exists(FakeGoogleFilePicker));
    assert.equal(wrapper.find(Button).length, 3);
  });

  it('shows URL selection dialog when "Enter URL" button is clicked', () => {
    const wrapper = renderFilePicker();

    const btn = wrapper.find('Button[label="Enter URL of web page or PDF"]');
    interact(wrapper, () => {
      btn.props().onClick();
    });

    assert.isTrue(wrapper.exists(FakeURLPicker));
  });

  it('submits a URL when a URL is selected', () => {
    const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
    const wrapper = renderFilePicker({ defaultActiveDialog: 'url', onSubmit });

    const picker = wrapper.find(FakeURLPicker);
    interact(wrapper, () => {
      picker.props().onSelectURL('https://example.com');
    });

    assert.called(onSubmit);
    assert.deepEqual(
      getContentItem(wrapper),
      contentItemForUrl(fakeConfig.ltiLaunchUrl, 'https://example.com')
    );
  });

  it('shows LMS file dialog when "Select PDF from <LMS Name>" is clicked', () => {
    const wrapper = renderFilePicker();

    const btn = wrapper.find('Button[label="Select PDF from Shiny LMS"]');
    interact(wrapper, () => {
      btn.props().onClick();
    });

    assert.isTrue(wrapper.exists(FakeLMSFilePicker));
  });

  it('submits an LMS file when an LMS file is selected', () => {
    const onSubmit = sinon.stub().callsFake(e => e.preventDefault());
    const wrapper = renderFilePicker({ defaultActiveDialog: 'lms', onSubmit });
    const file = { id: 123 };

    const picker = wrapper.find(FakeLMSFilePicker);
    interact(wrapper, () => {
      picker.props().onSelectFile(file);
    });

    assert.called(onSubmit);
    assert.deepEqual(
      getContentItem(wrapper),
      contentItemForLmsFile(fakeConfig.ltiLaunchUrl, file)
    );
  });

  it('shows Google Drive picker when "Select PDF from Google Drive is clicked', () => {
    const wrapper = renderFilePicker();

    const btn = wrapper.find('Button[label="Select PDF from Google Drive"]');
    interact(wrapper, () => {
      btn.props().onClick();
    });

    assert.isTrue(wrapper.exists(FakeGoogleFilePicker));
  });
});
