import { mockImportedComponents } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

import { Config } from '../../config';
import EmailNotificationsApp, { $imports } from '../EmailNotificationsApp';

describe('EmailNotificationsApp', () => {
  const emailNotificationsConfig = {
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

  function createComponent() {
    return mount(
      <Config.Provider value={{ emailNotifications: emailNotificationsConfig }}>
        <EmailNotificationsApp />
      </Config.Provider>
    );
  }

  it('loads preferences from config', () => {
    const wrapper = createComponent();
    const preferencesComponent = wrapper.find('EmailNotificationsPreferences');

    assert.isTrue(preferencesComponent.exists());
    assert.equal(
      preferencesComponent.prop('selectedDays'),
      emailNotificationsConfig
    );
  });

  it('allows selected days to be updated', () => {
    const wrapper = createComponent();
    const newSelectedDays = {
      mon: false,
      wed: true,
    };

    wrapper
      .find('EmailNotificationsPreferences')
      .props()
      .updateSelectedDays(newSelectedDays);
    wrapper.update();

    assert.deepEqual(
      wrapper.find('EmailNotificationsPreferences').prop('selectedDays'),
      {
        ...emailNotificationsConfig,
        ...newSelectedDays,
      }
    );
  });

  it('when preferences are saved it sets saving to true', () => {
    const wrapper = createComponent();

    wrapper.find('EmailNotificationsPreferences').props().onSave();
    wrapper.update();

    assert.isTrue(wrapper.find('EmailNotificationsPreferences').prop('saving'));
  });
});
