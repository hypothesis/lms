import { mockImportedComponents } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

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

  function createComponent(flashMessage = null) {
    const emailPreferences = { selectedDays, flashMessage };

    return mount(
      <Config.Provider value={{ emailPreferences }}>
        <EmailPreferencesApp />
      </Config.Provider>,
    );
  }

  function updateSelectedDays(wrapper, newSelectedDays) {
    wrapper
      .find('EmailPreferences')
      .props()
      .updateSelectedDays(newSelectedDays);
    wrapper.update();
  }

  function getToastMessages(wrapper) {
    const { messages } = wrapper.find('ToastMessages').props();
    return messages;
  }

  it('loads preferences from config', () => {
    const wrapper = createComponent();
    const preferencesComponent = wrapper.find('EmailPreferences');

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

    assert.deepEqual(wrapper.find('EmailPreferences').prop('selectedDays'), {
      ...selectedDays,
      ...newSelectedDays,
    });
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
      const wrapper = createComponent('Success!');

      assert.equal(getToastMessages(wrapper).length, 1);
      updateSelectedDays(wrapper, newSelectedDays);
      assert.equal(getToastMessages(wrapper).length, toastMessagesAfterUpdate);
    });
  });

  it('sets saving to true when preferences are saved', () => {
    const wrapper = createComponent();

    wrapper.find('EmailPreferences').props().onSave();
    wrapper.update();

    assert.isTrue(wrapper.find('EmailPreferences').prop('saving'));
  });

  [
    { flashMessageFromConfig: null, expectedToastMessages: 0 },
    {
      flashMessageFromConfig: 'Preferences saved',
      expectedToastMessages: 1,
    },
  ].forEach(({ flashMessageFromConfig, expectedToastMessages }) => {
    it('renders flash message as toast message', () => {
      const wrapper = createComponent(flashMessageFromConfig);
      const messages = getToastMessages(wrapper);

      assert.equal(messages.length, expectedToastMessages);
    });
  });
});
