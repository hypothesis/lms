import { mount } from '@hypothesis/frontend-testing';

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
        title={null}
        {...props}
      />,
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

  [
    {
      groupSet: null,
      fieldValue: '',
    },
    {
      groupSet: 'abcdef',
      fieldValue: 'abcdef',
    },
  ].forEach(({ groupSet, fieldValue }) => {
    it('adds a `group_set` hidden form field', () => {
      const content = { type: 'url', url: 'https://example.com/' };
      const formFields = createComponent({
        content,
        groupSet,
      });

      const groupSetField = formFields.find('input[name="group_set"]');
      assert.isTrue(groupSetField.exists());
      assert.equal(groupSetField.prop('value'), fieldValue);
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

  it('renders `title` field if `title` prop is set', () => {
    const formFields = createComponent({
      content: { type: 'url', url: 'https://example.com/' },
      title: 'Example assignment',
    });
    const titleField = formFields.find('input[name="title"]');
    assert.isTrue(titleField.exists());
    assert.equal(titleField.prop('value'), 'Example assignment');
  });

  it('renders `auto_grading_config` if `autoGradingConfig` prop is set', () => {
    const autoGradingConfig = {
      grading_type: 'scaled',
      activity_calculation: 'separate',
      required_annotations: 10,
      required_replies: 5,
    };
    const formFields = createComponent({
      content: { type: 'url', url: 'https://example.com/' },
      autoGradingConfig,
    });
    const configField = formFields.find('input[name="auto_grading_config"]');

    assert.isTrue(configField.exists());
    assert.equal(configField.prop('value'), JSON.stringify(autoGradingConfig));
  });
});
