import { mount } from 'enzyme';

import { Config } from '../../config';
import EmailNotificationsApp from '../EmailNotificationsApp';

describe('EmailNotificationsApp', () => {
  const emailNotificationsConfig = {
    'instructor_email_digests.days.mon': true,
    'instructor_email_digests.days.tue': true,
    'instructor_email_digests.days.wed': false,
    'instructor_email_digests.days.thu': false,
    'instructor_email_digests.days.fri': true,
    'instructor_email_digests.days.sat': false,
    'instructor_email_digests.days.sun': true,
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
      'instructor_email_digests.days.mon': false,
      'instructor_email_digests.days.wed': true,
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
