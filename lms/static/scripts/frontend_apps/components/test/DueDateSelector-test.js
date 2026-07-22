import { Select } from '@hypothesis/frontend-shared';
import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import { createRef } from 'preact';
import { act } from 'preact/test-utils';

import DueDateSelector from '../DueDateSelector';

describe('DueDateSelector', () => {
  let fakeOnChange;

  beforeEach(() => {
    fakeOnChange = sinon.stub();
  });

  function createComponent(dueDate = null, min = undefined, selectorRef) {
    return mount(
      <DueDateSelector
        dueDate={dueDate}
        onChange={fakeOnChange}
        min={min}
        selectorRef={selectorRef}
      />,
      // Connect to the DOM so the popovers (which use the native popover API)
      // can toggle.
      { connected: true },
    );
  }

  const dateInput = wrapper =>
    wrapper.find('input[data-testid="due-date-input"]');
  const timeSelect = wrapper => wrapper.find(Select);
  const errorMessage = wrapper =>
    wrapper.find('div[data-testid="due-date-error"]');

  // Open the time dropdown. Its options are only rendered while it is open.
  const openTimeSelect = wrapper => {
    timeSelect(wrapper)
      .find('button[data-testid="select-toggle-button"]')
      .simulate('click');
    wrapper.update();
  };
  const timeSelectOptions = wrapper => timeSelect(wrapper).find(Select.Option);

  // Each helper re-renders before returning. The change handlers close over
  // the current date and time, so acting twice against a stale wrapper would
  // run the second change with the values from before the first one.
  const changeDate = (wrapper, value) => {
    act(() => dateInput(wrapper).props().onChange({ target: { value } }));
    wrapper.update();
  };
  const changeTime = (wrapper, value) => {
    act(() => timeSelect(wrapper).props().onChange(value));
    wrapper.update();
  };

  it('splits the selected due date across the date and time fields', () => {
    const wrapper = createComponent('2026-06-11T14:30');

    assert.equal(dateInput(wrapper).prop('value'), '2026-06-11');
    assert.equal(timeSelect(wrapper).prop('value'), '14:30');
    assert.include(timeSelect(wrapper).text(), '2:30 PM');
  });

  it('renders empty fields when no due date is set', () => {
    const wrapper = createComponent(null);

    assert.equal(dateInput(wrapper).prop('value'), '');
    assert.equal(timeSelect(wrapper).prop('value'), '');
    assert.include(timeSelect(wrapper).text(), 'Select a time');
  });

  it('reports no due date while only a date has been picked', () => {
    const wrapper = createComponent();

    changeDate(wrapper, '2026-06-11');

    // The time is not guessed on the instructor's behalf; the step is blocked
    // until they pick one.
    assert.calledWith(fakeOnChange, null);
    wrapper.update();
    assert.equal(timeSelect(wrapper).prop('value'), '');
  });

  it('keeps an already-entered time when a date is picked', () => {
    const wrapper = createComponent();

    changeTime(wrapper, '09:00');
    changeDate(wrapper, '2026-06-11');

    assert.calledWith(fakeOnChange, '2026-06-11T09:00');
  });

  it('invokes onChange with the combined value when the time changes', () => {
    const wrapper = createComponent('2026-06-11T23:59');

    changeTime(wrapper, '08:15');

    assert.calledWith(fakeOnChange, '2026-06-11T08:15');
  });

  it('reports no due date when the time is cleared', () => {
    const wrapper = createComponent('2026-06-11T14:30');

    changeTime(wrapper, '');

    assert.calledWith(fakeOnChange, null);
  });

  it('reports no due date while only a time has been entered', () => {
    const wrapper = createComponent();

    changeTime(wrapper, '09:00');

    assert.calledWith(fakeOnChange, null);
  });

  it('requires the date once a time has been entered', () => {
    const wrapper = createComponent();

    assert.isNotTrue(dateInput(wrapper).prop('required'));

    changeTime(wrapper, '09:00');
    wrapper.update();

    // Lets `validate` catch the half-entered value via the input's own
    // constraints rather than silently dropping the time.
    assert.isTrue(dateInput(wrapper).prop('required'));
  });

  it('clears both fields when the date is cleared', () => {
    const wrapper = createComponent('2026-06-11T14:30');

    changeDate(wrapper, '');

    assert.calledWith(fakeOnChange, null);
    wrapper.update();
    assert.equal(dateInput(wrapper).prop('value'), '');
    assert.equal(timeSelect(wrapper).prop('value'), '');
  });

  it('constrains the date to the minimum', () => {
    const wrapper = createComponent(null, '2026-06-11T14:30');

    assert.equal(dateInput(wrapper).prop('min'), '2026-06-11');
  });

  it('offers times at half-hour steps, labelled for a 12-hour clock', () => {
    const wrapper = createComponent();
    openTimeSelect(wrapper);
    const options = timeSelectOptions(wrapper);

    // A placeholder plus one option per half hour.
    assert.equal(options.length, 1 + 48);
    assert.equal(options.at(0).prop('value'), '');

    const labelFor = value =>
      options.filterWhere(o => o.prop('value') === value).text();
    assert.equal(labelFor('00:00'), '12:00 AM');
    assert.equal(labelFor('00:30'), '12:30 AM');
    assert.equal(labelFor('12:00'), '12:00 PM');
    assert.equal(labelFor('13:30'), '1:30 PM');
    assert.equal(labelFor('23:30'), '11:30 PM');
  });

  it('keeps an existing time that is not on the half-hour grid', () => {
    // An assignment saved before this dropdown existed can hold any minute;
    // dropping it would silently change the due date.
    const wrapper = createComponent('2026-06-11T14:45');
    openTimeSelect(wrapper);

    const values = timeSelectOptions(wrapper).map(o => o.prop('value'));
    assert.include(values, '14:45');
    assert.equal(timeSelect(wrapper).prop('value'), '14:45');
  });

  it('disables past times only on the earliest selectable date', () => {
    const wrapper = createComponent(null, '2026-06-11T14:30');
    const disabled = value =>
      timeSelectOptions(wrapper)
        .filterWhere(o => o.prop('value') === value)
        .prop('disabled');

    // On the earliest date, times before the minimum are in the past.
    changeDate(wrapper, '2026-06-11');
    openTimeSelect(wrapper);
    assert.isTrue(disabled('14:00'));
    assert.isFalse(disabled('15:00'));

    // On any later date, every time of day is still in the future.
    changeDate(wrapper, '2026-06-12');
    assert.isFalse(disabled('14:00'));
  });

  describe('validate', () => {
    let selectorRef;

    const createWithHandle = (dueDate = null, min = undefined) => {
      selectorRef = createRef();
      return createComponent(dueDate, min, selectorRef);
    };

    const validate = wrapper => {
      let valid;
      act(() => {
        valid = selectorRef.current.validate();
      });
      wrapper.update();
      return valid;
    };

    it('accepts an empty due date', () => {
      const wrapper = createWithHandle();

      assert.isTrue(validate(wrapper));
      assert.isFalse(errorMessage(wrapper).exists());
    });

    it('accepts a complete future due date', () => {
      const wrapper = createWithHandle('2026-06-11T14:30', '2026-06-11T10:00');

      assert.isTrue(validate(wrapper));
      assert.isFalse(errorMessage(wrapper).exists());
    });

    it('rejects a date without a time', () => {
      const wrapper = createWithHandle();

      changeDate(wrapper, '2026-06-11');

      assert.isFalse(validate(wrapper));
      assert.equal(errorMessage(wrapper).text(), 'Select a time.');
    });

    it('rejects a time without a date', () => {
      const wrapper = createWithHandle();

      changeTime(wrapper, '09:00');

      // The date field is a native input carrying `required`, so the browser
      // reports this one rather than the inline message.
      assert.isFalse(validate(wrapper));
      assert.isFalse(errorMessage(wrapper).exists());
    });

    it('rejects a due date that is no longer in the future', () => {
      // Each field holds a value that was valid when picked; only the combined
      // comparison can see that the clock has since passed it.
      const wrapper = createWithHandle('2026-06-11T10:00', '2026-06-11T14:30');

      assert.isFalse(validate(wrapper));
      assert.equal(
        errorMessage(wrapper).text(),
        'The due date must be in the future.',
      );
    });

    it('clears the error as soon as the value changes', () => {
      const wrapper = createWithHandle();

      changeDate(wrapper, '2026-06-11');
      assert.isFalse(validate(wrapper));
      assert.isTrue(errorMessage(wrapper).exists());

      changeTime(wrapper, '09:00');
      assert.isFalse(errorMessage(wrapper).exists());
    });
  });

  it('shows the due date explanation in a popover instead of inline', () => {
    const wrapper = createComponent();
    // The time dropdown renders its own (second) popover; the explanation
    // lives in the first one, anchored to the info icon.
    const popover = () => wrapper.find('Popover').first();
    const explanation =
      'The point where annotations are no longer tallied in auto grading.';

    // The explanation is not rendered inline, only inside the (closed) popover.
    assert.isFalse(popover().prop('open'));

    // Clicking the info icon opens the popover with the explanation.
    act(() => wrapper.find('IconButton').props().onClick());
    wrapper.update();

    assert.isTrue(popover().prop('open'));
    assert.include(popover().text(), explanation);

    // The popover can be dismissed.
    act(() => popover().props().onClose());
    wrapper.update();
    assert.isFalse(popover().prop('open'));
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
