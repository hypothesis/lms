import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import DueDateSelector from '../DueDateSelector';

describe('DueDateSelector', () => {
  let fakeOnChange;

  beforeEach(() => {
    fakeOnChange = sinon.stub();
  });

  function createComponent(dueDate = null) {
    return mount(
      <DueDateSelector dueDate={dueDate} onChange={fakeOnChange} />,
      // Connect to the DOM so the info `Popover` (which uses the native popover
      // API) can toggle.
      { connected: true },
    );
  }

  const dateInput = wrapper =>
    wrapper.find('input[data-testid="due-date-input"]');

  it('reflects the selected due date', () => {
    const wrapper = createComponent('2026-06-11');
    assert.equal(dateInput(wrapper).prop('value'), '2026-06-11');
  });

  it('renders an empty value when no due date is set', () => {
    const wrapper = createComponent(null);
    assert.equal(dateInput(wrapper).prop('value'), '');
  });

  it('invokes onChange with the selected date', () => {
    const wrapper = createComponent();

    act(() =>
      dateInput(wrapper)
        .props()
        .onChange({ target: { value: '2026-06-11' } }),
    );

    assert.calledWith(fakeOnChange, '2026-06-11');
  });

  it('invokes onChange with null when the date is cleared', () => {
    const wrapper = createComponent('2026-06-11');

    act(() =>
      dateInput(wrapper)
        .props()
        .onChange({ target: { value: '' } }),
    );

    assert.calledWith(fakeOnChange, null);
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
