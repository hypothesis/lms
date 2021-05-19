import { mount } from 'enzyme';
import { createElement } from 'preact';

import {
  contentItemForLmsFile,
  contentItemForUrl,
  contentItemForVitalSourceBook,
} from '../../utils/content-item';

import FilePickerFormFields from '../FilePickerFormFields';

describe('FilePickerFormFields', () => {
  const launchURL = 'https://testlms.hypothes.is/lti_launch';
  const staticFormFields = {
    lti_message_type: 'ContentItemSelection',
    lti_version: 'LTI-1p0',
    oauth_stuff: 'foobar',
  };

  function createComponent(props = {}) {
    return mount(
      <FilePickerFormFields
        content={{ type: 'url', url: 'https://testsite.example/' }}
        formFields={staticFormFields}
        ltiLaunchURL={launchURL}
        {...props}
      />
    );
  }

  const getContentItem = wrapper =>
    JSON.parse(wrapper.find('input[name="content_items"]').prop('value'));

  it('renders static form fields provided by backend', () => {
    const formFields = createComponent();

    Object.entries(staticFormFields).forEach(([name, value]) => {
      const field = formFields
        .find('input[type="hidden"]')
        .filter(`[name="${name}"]`);
      assert.isTrue(field.exists());
      assert.equal(field.prop('value'), value);
    });
  });

  describe('content_items field', () => {
    it('renders content_items field for URL content', () => {
      const formFields = createComponent({
        content: { type: 'url', url: 'https://example.com/' },
      });
      const contentItems = getContentItem(formFields);
      assert.deepEqual(
        contentItems,
        contentItemForUrl(launchURL, 'https://example.com/')
      );
    });

    it('renders content_items field for LMS file content', () => {
      const file = { id: 123 };
      const formFields = createComponent({
        content: { type: 'file', file },
      });
      const contentItems = getContentItem(formFields);
      assert.deepEqual(contentItems, contentItemForLmsFile(launchURL, file));
    });

    it('renders content_items field for VitalSource book content', () => {
      const formFields = createComponent({
        content: { type: 'vitalsource', bookID: 'test-book', cfi: 'test-cfi' },
      });
      const contentItems = getContentItem(formFields);
      assert.deepEqual(
        contentItems,
        contentItemForVitalSourceBook(launchURL, 'test-book', 'test-cfi')
      );
    });
  });

  it('renders `document_url` field for URL content', () => {
    const formFields = createComponent({
      content: { type: 'url', url: 'https://example.com/' },
    });
    const documentURLField = formFields.find('input[name="document_url"]');
    assert.isTrue(documentURLField.exists());
    assert.equal(documentURLField.prop('value'), 'https://example.com/');
  });
});
