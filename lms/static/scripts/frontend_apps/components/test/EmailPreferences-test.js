import { mount } from 'enzyme';

import EmailPreferences from '../EmailPreferences';

describe('EmailPreferences', () => {
  let fakeUpdateSelectedDays;
  const initialSelectedDays = {
    sun: true,
    mon: true,
    tue: false,
    wed: true,
    thu: false,
    fri: false,
    sat: true,
  };

  beforeEach(() => {
    fakeUpdateSelectedDays = sinon.stub();
  });

  function createComponent(props = {}) {
    return mount(
      <EmailPreferences
        selectedDays={initialSelectedDays}
        updateSelectedDays={fakeUpdateSelectedDays}
        {...props}
      />,
    );
  }

  function getCheckbox(wrapper, day) {
    return wrapper.find(`Checkbox[data-testid="${day}-checkbox"]`);
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
      sun: true,
      mon: true,
      tue: true,
      wed: true,
      thu: true,
      fri: true,
      sat: true,
    });
  });

  it('can unselect all checkboxes', () => {
    const wrapper = createComponent();

    wrapper.find('button[data-testid="select-none-button"]').simulate('click');

    assert.calledWith(fakeUpdateSelectedDays, {
      sun: false,
      mon: false,
      tue: false,
      wed: false,
      thu: false,
      fri: false,
      sat: false,
    });
  });

  ['sun', 'mon', 'thu'].forEach(day => {
    it('lets individual days be changed', () => {
      const wrapper = createComponent();

      getCheckbox(wrapper, day).props().onChange();

      assert.calledWith(fakeUpdateSelectedDays, {
        [day]: !initialSelectedDays[day],
      });
    });
  });

  [true, false].forEach(saving => {
    it('disables save button while saving', () => {
      const wrapper = createComponent({ saving });
      const button = wrapper.find('Button[data-testid="save-button"]');

      assert.equal(button.prop('disabled'), saving);
    });
  });

  it('saves preferences', () => {
    const onSave = sinon.stub();
    const wrapper = createComponent({ onSave });

    wrapper.find('form').simulate('submit');

    assert.called(onSave);
  });
});
