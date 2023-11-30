import { mount } from 'enzyme';

import EmailNotificationsPreferences from '../EmailNotificationsPreferences';

describe('EmailNotificationsPreferences', () => {
  let fakeUpdateSelectedDays;
  const initialSelectedDays = {
    'instructor_email_digests.days.sun': true,
    'instructor_email_digests.days.mon': true,
    'instructor_email_digests.days.tue': false,
    'instructor_email_digests.days.wed': true,
    'instructor_email_digests.days.thu': false,
    'instructor_email_digests.days.fri': false,
    'instructor_email_digests.days.sat': true,
  };

  beforeEach(() => {
    fakeUpdateSelectedDays = sinon.stub();
  });

  function createComponent() {
    return mount(
      <EmailNotificationsPreferences
        selectedDays={initialSelectedDays}
        updateSelectedDays={fakeUpdateSelectedDays}
      />
    );
  }

  function getCheckbox(wrapper, day) {
    return wrapper.find(
      `Checkbox[data-testid="instructor_email_digests.days.${day}-checkbox"]`
    );
  }

  it('initially selects appropriate checkboxes', () => {
    const wrapper = createComponent();

    assert.isTrue(getCheckbox(wrapper, 'sun').prop('checked'));
    assert.isTrue(getCheckbox(wrapper, 'mon').prop('checked'));
    assert.isFalse(getCheckbox(wrapper, 'tue').prop('checked'));
    assert.isTrue(getCheckbox(wrapper, 'wed').prop('checked'));
    assert.isFalse(getCheckbox(wrapper, 'thu').prop('checked'));
    assert.isFalse(getCheckbox(wrapper, 'fri').prop('checked'));
    assert.isTrue(getCheckbox(wrapper, 'sat').prop('checked'));
  });

  it('can select all checkboxes', () => {
    const wrapper = createComponent();

    wrapper.find('button[data-testid="select-all-button"]').simulate('click');

    assert.calledWith(fakeUpdateSelectedDays, {
      'instructor_email_digests.days.sun': true,
      'instructor_email_digests.days.mon': true,
      'instructor_email_digests.days.tue': true,
      'instructor_email_digests.days.wed': true,
      'instructor_email_digests.days.thu': true,
      'instructor_email_digests.days.fri': true,
      'instructor_email_digests.days.sat': true,
    });
  });

  it('can unselect all checkboxes', () => {
    const wrapper = createComponent();

    wrapper.find('button[data-testid="select-none-button"]').simulate('click');

    assert.calledWith(fakeUpdateSelectedDays, {
      'instructor_email_digests.days.sun': false,
      'instructor_email_digests.days.mon': false,
      'instructor_email_digests.days.tue': false,
      'instructor_email_digests.days.wed': false,
      'instructor_email_digests.days.thu': false,
      'instructor_email_digests.days.fri': false,
      'instructor_email_digests.days.sat': false,
    });
  });

  ['sun', 'mon', 'thu'].forEach(day => {
    it('lets individual days be changed', () => {
      const wrapper = createComponent();
      const dayKey = `instructor_email_digests.days.${day}`;

      getCheckbox(wrapper, day).props().onChange();

      assert.calledWith(fakeUpdateSelectedDays, {
        [dayKey]: !initialSelectedDays[dayKey],
      });
    });
  });
});
