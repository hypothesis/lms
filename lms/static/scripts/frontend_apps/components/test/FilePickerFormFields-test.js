import { mount } from 'enzyme';

import FilePickerFormFields from '../FilePickerFormFields';

describe('FilePickerFormFields', () => {
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

  it('adds a `group_set` hidden form field', () => {
    const content = { type: 'url', url: 'https://example.com/' };
    const formFields = createComponent({
      content,
      groupSet: 'groupSet1',
    });

    assert.isTrue(formFields.find('input[name="group_set"]').exists());
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
