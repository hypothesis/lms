import { mockImportedComponents } from '@hypothesis/frontend-testing';
import { mount } from '@hypothesis/frontend-testing';

import { Config } from '../../config';
import EmailPreferencesApp, { $imports } from '../EmailPreferencesApp';

describe('EmailPreferencesApp', () => {
  const selectedDays = {
    mon: true,
    tue: true,
    wed: false,
    thu: false,
    fri: true,
    sat: false,
    sun: true,
  };

  beforeEach(() => {
    $imports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    $imports.$restore();
  });

  function createComponent({
    flashMessage = null,
    isInstructor = true,
    mentionsEnabled = false,
  } = {}) {
    const emailPreferences = {
      selectedDays,
      flashMessage,
      is_instructor: isInstructor,
      mention_email_feature_enabled: mentionsEnabled,
    };

    return mount(
      <Config.Provider value={{ emailPreferences }}>
        <EmailPreferencesApp />
      </Config.Provider>,
    );
  }

  function updateSelectedDays(wrapper, newSelectedDays) {
    wrapper
      .find('EmailDigestPreferences')
      .props()
      .onSelectedDaysChange(newSelectedDays);
    wrapper.update();
  }

  function getToastMessages(wrapper) {
    const { messages } = wrapper.find('ToastMessages').props();
    return messages;
  }

  it('loads preferences from config', () => {
    const wrapper = createComponent();
    const preferencesComponent = wrapper.find('EmailDigestPreferences');

    assert.isTrue(preferencesComponent.exists());
    assert.equal(preferencesComponent.prop('selectedDays'), selectedDays);
  });

  it('allows selected days to be updated', () => {
    const wrapper = createComponent();
    const newSelectedDays = {
      mon: false,
      wed: true,
    };

    updateSelectedDays(wrapper, newSelectedDays);

    assert.deepEqual(
      wrapper.find('EmailDigestPreferences').prop('selectedDays'),
      {
        ...selectedDays,
        ...newSelectedDays,
      },
    );
  });

  [
    {
      newSelectedDays: {
        mon: false,
        wed: true,
      },
      toastMessagesAfterUpdate: 0,
    },
    {
      newSelectedDays: selectedDays,
      toastMessagesAfterUpdate: 1,
    },
  ].forEach(({ newSelectedDays, toastMessagesAfterUpdate }) => {
    it('hides toast message if selected days are updated', () => {
      const wrapper = createComponent({ flashMessage: 'Success!' });

      assert.equal(getToastMessages(wrapper).length, 1);
      updateSelectedDays(wrapper, newSelectedDays);
      assert.equal(getToastMessages(wrapper).length, toastMessagesAfterUpdate);
    });
  });

  it('disables submit button when preferences are being saved', () => {
    const wrapper = createComponent();

    wrapper.find('form').simulate('submit');

    assert.isTrue(
      wrapper.find('Button[data-testid="save-button"]').prop('disabled'),
    );
  });

  [
    { flashMessageFromConfig: null, expectedToastMessages: 0 },
    {
      flashMessageFromConfig: 'Preferences saved',
      expectedToastMessages: 1,
    },
  ].forEach(({ flashMessageFromConfig, expectedToastMessages }) => {
    it('renders flash message as toast message', () => {
      const wrapper = createComponent({ flashMessage: flashMessageFromConfig });
      const messages = getToastMessages(wrapper);

      assert.equal(messages.length, expectedToastMessages);
    });
  });

  [true, false].forEach(isInstructor => {
    it('shows EmailDigestPreferences only for instructors', () => {
      const wrapper = createComponent({ isInstructor });
      assert.equal(wrapper.exists('EmailDigestPreferences'), isInstructor);
    });
  });

  [true, false].forEach(mentionsEnabled => {
    it('shows EmailMentionsPreferences only if mentions are enabled', () => {
      const wrapper = createComponent({ mentionsEnabled });
      assert.equal(wrapper.exists('EmailMentionsPreferences'), mentionsEnabled);
    });
  });
});
