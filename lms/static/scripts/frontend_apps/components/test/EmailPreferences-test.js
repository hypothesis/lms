import { mount } from 'enzyme';

import EmailPreferences from '../EmailPreferences';

describe('EmailPreferences', () => {
  let fakeUpdateSelectedDays;
  const wrappers = [];
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

  afterEach(() => {
    wrappers.forEach(wrapper => wrapper.unmount());
  });

  function createComponent(props = {}) {
    const container = document.createElement('div');
    document.body.append(container);

    const wrapper = mount(
      <EmailPreferences
        selectedDays={initialSelectedDays}
        updateSelectedDays={fakeUpdateSelectedDays}
        {...props}
      />,
      { attachTo: container }
    );
    wrappers.push(wrapper);

    return wrapper;
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

  [
    { message: 'Error', status: 'error' },
    { message: 'Success', status: 'success' },
    undefined,
  ].forEach(result => {
    it('displays error message if provided', () => {
      const wrapper = createComponent({ result });
      assert.equal(wrapper.exists('Callout'), !!result);
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

  it('can navigate checkboxes with the keyboard', async () => {
    const wrapper = createComponent();
    const getCheckbox = index =>
      wrapper.find('input[type="checkbox"]').at(index).getDOMNode();
    const pressArrow = key =>
      document.activeElement.dispatchEvent(
        new KeyboardEvent('keydown', {
          bubbles: true,
          cancelable: true,
          key,
        })
      );

    // Focus first checkbox
    getCheckbox(0).focus();
    assert.equal(document.activeElement, getCheckbox(0));

    // Press down arrow three times
    pressArrow('ArrowDown');
    pressArrow('ArrowDown');
    pressArrow('ArrowDown');
    assert.equal(document.activeElement, getCheckbox(3));

    // Press down arrow once more
    pressArrow('ArrowDown');
    assert.equal(document.activeElement, getCheckbox(4));

    // Press up arrow twice
    pressArrow('ArrowUp');
    pressArrow('ArrowUp');
    assert.equal(document.activeElement, getCheckbox(2));
  });
});
