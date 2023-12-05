import { mount } from 'enzyme';

import { Config } from '../../config';
import EmailNotificationsApp from '../EmailNotificationsApp';

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
});
