import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import DueDateSelector from '../DueDateSelector';

describe('DueDateSelector', () => {
  let fakeOnChange;

  beforeEach(() => {
    fakeOnChange = sinon.stub();
  });

  function createComponent(dueDate = null, min = undefined) {
    return mount(
      <DueDateSelector dueDate={dueDate} onChange={fakeOnChange} min={min} />,
      // Connect to the DOM so the info `Popover` (which uses the native popover
      // API) can toggle.
      { connected: true },
    );
  }

  const dateInput = wrapper =>
    wrapper.find('input[data-testid="due-date-input"]');
  const timeInput = wrapper =>
    wrapper.find('select[data-testid="due-date-time-input"]');
  const timeOptionValues = wrapper =>
    timeInput(wrapper)
      .find('option')
      .map(option => option.prop('value'));

  // Each helper re-renders before returning. The change handlers close over
  // the current date and time, so acting twice against a stale wrapper would
  // run the second change with the values from before the first one.
  const changeDate = (wrapper, value) => {
    act(() => dateInput(wrapper).props().onChange({ target: { value } }));
    wrapper.update();
  };
  const changeTime = (wrapper, value) => {
    act(() => timeInput(wrapper).props().onChange({ target: { value } }));
    wrapper.update();
  };

  it('splits the selected due date across the date and time fields', () => {
    const wrapper = createComponent('2026-06-11T14:30');

    assert.equal(dateInput(wrapper).prop('value'), '2026-06-11');
    assert.equal(timeInput(wrapper).prop('value'), '14:30');
  });

  it('renders empty fields when no due date is set', () => {
    const wrapper = createComponent(null);

    assert.equal(dateInput(wrapper).prop('value'), '');
    assert.equal(timeInput(wrapper).prop('value'), '');
  });

  it('reports no due date while only a date has been picked', () => {
    const wrapper = createComponent();

    changeDate(wrapper, '2026-06-11');

    // The time is not guessed on the instructor's behalf; the step is blocked
    // until they pick one.
    assert.calledWith(fakeOnChange, null);
    wrapper.update();
    assert.equal(timeInput(wrapper).prop('value'), '');
  });

  it('requires the time once a date has been picked', () => {
    const wrapper = createComponent();

    assert.isNotTrue(timeInput(wrapper).prop('required'));

    changeDate(wrapper, '2026-06-11');
    wrapper.update();

    assert.isTrue(timeInput(wrapper).prop('required'));
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

    // Lets the parent's `reportValidity()` catch the half-entered value rather
    // than silently dropping the time.
    assert.isTrue(dateInput(wrapper).prop('required'));
  });

  it('clears both fields when the date is cleared', () => {
    const wrapper = createComponent('2026-06-11T14:30');

    changeDate(wrapper, '');

    assert.calledWith(fakeOnChange, null);
    wrapper.update();
    assert.equal(dateInput(wrapper).prop('value'), '');
    assert.equal(timeInput(wrapper).prop('value'), '');
  });

  it('constrains the date to the minimum', () => {
    const wrapper = createComponent(null, '2026-06-11T14:30');

    assert.equal(dateInput(wrapper).prop('min'), '2026-06-11');
  });

  it('offers times at half-hour steps, labelled for a 12-hour clock', () => {
    const wrapper = createComponent();
    const options = timeInput(wrapper).find('option');

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

    assert.include(timeOptionValues(wrapper), '14:45');
    assert.equal(timeInput(wrapper).prop('value'), '14:45');
  });

  it('disables past times only on the earliest selectable date', () => {
    const wrapper = createComponent(null, '2026-06-11T14:30');
    const disabled = value =>
      timeInput(wrapper)
        .find('option')
        .filterWhere(o => o.prop('value') === value)
        .prop('disabled');

    // On the earliest date, times before the minimum are in the past.
    changeDate(wrapper, '2026-06-11');
    wrapper.update();
    assert.isTrue(disabled('14:00'));
    assert.isFalse(disabled('15:00'));

    // On any later date, every time of day is still in the future.
    changeDate(wrapper, '2026-06-12');
    wrapper.update();
    assert.isFalse(disabled('14:00'));
  });

  it('shows the due date explanation in a popover instead of inline', () => {
    const wrapper = createComponent();
    const popover = () => wrapper.find('Popover');
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
