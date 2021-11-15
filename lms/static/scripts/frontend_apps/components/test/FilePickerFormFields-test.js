import { mount } from 'enzyme';

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
        groupSet={null}
        ltiLaunchURL={launchURL}
        {...props}
      />
    );
  }

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

  it('renders `content_items` field for content', () => {
    const content = { type: 'url', url: 'https://example.com/' };
    const formFields = createComponent({
      content,
    });
    const contentItems = JSON.parse(
      formFields.find('input[name="content_items"]').prop('value')
    );
    assert.deepEqual(contentItems, contentItemForContent(launchURL, content));
  });

  it('adds `group_set` query param to LTI launch URL if `groupSet` prop is specified', () => {
    const content = { type: 'url', url: 'https://example.com/' };
    const formFields = createComponent({
      content,
      groupSet: 'groupSet1',
    });
    const contentItems = JSON.parse(
      formFields.find('input[name="content_items"]').prop('value')
    );
    assert.deepEqual(
      contentItems,
      contentItemForContent(launchURL, content, {
        group_set: 'groupSet1',
      })
    );
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
