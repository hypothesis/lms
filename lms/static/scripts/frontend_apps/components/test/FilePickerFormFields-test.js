import { mount } from 'enzyme';
import { createElement } from 'preact';

import { contentItemForContent } from '../../utils/content-item';

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
    it('renders content_items field for content', () => {
      const content = { type: 'url', url: 'https://example.com/' };
      const formFields = createComponent({
        content,
      });
      const contentItems = getContentItem(formFields);
      assert.deepEqual(contentItems, contentItemForContent(launchURL, content));
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
