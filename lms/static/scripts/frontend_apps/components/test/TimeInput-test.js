import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import TimeInput from '../TimeInput';

describe('TimeInput', () => {
  let fakeOnChange;
  let fakeOnCommit;

  // A short list exercising both plain and disabled suggestions.
  const defaultOptions = [
    { label: '3:00 AM' },
    { label: '3:30 AM', disabled: true },
    { label: '3:00 PM' },
  ];

  beforeEach(() => {
    fakeOnChange = sinon.stub();
    fakeOnCommit = sinon.stub();
  });

  function createComponent(value = '', options = defaultOptions) {
    return mount(
      <TimeInput
        value={value}
        onChange={fakeOnChange}
        onCommit={fakeOnCommit}
        options={options}
      />,
      // Connect to the DOM so the dropdown (native popover API) can toggle.
      { connected: true },
    );
  }

  const input = wrapper => wrapper.find('input[data-testid="time-input"]');
  const listOptions = wrapper => wrapper.find('li[role="option"]');
  const optionLabels = wrapper => listOptions(wrapper).map(o => o.text());
  const highlightedId = wrapper => input(wrapper).prop('aria-activedescendant');
  const highlightedText = wrapper => {
    const id = highlightedId(wrapper);
    return id ? wrapper.find(`li[id="${id}"]`).text() : null;
  };

  // Mirror the controlled-component contract: the parent echoes reported
  // text back through the `value` prop.
  const typeText = (wrapper, text) => {
    act(() =>
      input(wrapper)
        .props()
        .onInput({ currentTarget: { value: text } }),
    );
    wrapper.setProps({ value: text });
    wrapper.update();
  };

  const clickInput = wrapper => {
    act(() => input(wrapper).props().onClick());
    wrapper.update();
  };

  const pressKey = (wrapper, key) => {
    const event = new KeyboardEvent('keydown', { key, cancelable: true });
    act(() => input(wrapper).props().onKeyDown(event));
    wrapper.update();
    return event;
  };

  const blurInput = (wrapper, relatedTarget = null) => {
    act(() => input(wrapper).props().onBlur({ relatedTarget }));
    wrapper.update();
  };

  it('renders the current text', () => {
    const wrapper = createComponent('3:00 PM');
    assert.equal(input(wrapper).prop('value'), '3:00 PM');
  });

  it('shows the suggestions when the input is clicked', () => {
    const wrapper = createComponent();

    // The dropdown contents are not rendered while it is closed.
    assert.equal(listOptions(wrapper).length, 0);
    assert.isFalse(input(wrapper).prop('aria-expanded'));

    clickInput(wrapper);

    assert.deepEqual(optionLabels(wrapper), ['3:00 AM', '3:30 AM', '3:00 PM']);
    assert.isTrue(input(wrapper).prop('aria-expanded'));

    // Clicking the input again keeps the dropdown open, with the highlight
    // where it was.
    clickInput(wrapper);
    assert.isTrue(input(wrapper).prop('aria-expanded'));
  });

  it('reports and filters as the user types', () => {
    const wrapper = createComponent();

    // Prefix-matching ignores case and spaces, and offers every period.
    typeText(wrapper, '3:0');

    assert.calledWith(fakeOnChange, '3:0');
    assert.deepEqual(optionLabels(wrapper), ['3:00 AM', '3:00 PM']);
  });

  it('shows an inert row when nothing matches', () => {
    const wrapper = createComponent();

    typeText(wrapper, '9:99');

    assert.deepEqual(optionLabels(wrapper), ['---']);
    assert.equal(listOptions(wrapper).prop('aria-disabled'), 'true');
    assert.isNull(highlightedText(wrapper));
  });

  it('chooses a suggestion on click', () => {
    const wrapper = createComponent();
    clickInput(wrapper);

    act(() => listOptions(wrapper).at(2).props().onClick());
    wrapper.update();

    assert.calledWith(fakeOnChange, '3:00 PM');
    assert.called(fakeOnCommit);
    assert.isFalse(input(wrapper).prop('aria-expanded'));
  });

  it('ignores clicks on disabled suggestions', () => {
    const wrapper = createComponent();
    clickInput(wrapper);

    act(() => listOptions(wrapper).at(1).props().onClick());
    wrapper.update();

    assert.notCalled(fakeOnChange);
    assert.notCalled(fakeOnCommit);
    assert.isTrue(input(wrapper).prop('aria-expanded'));
  });

  it('opens the dropdown with the arrow keys', () => {
    const wrapper = createComponent();

    pressKey(wrapper, 'ArrowDown');

    assert.isTrue(input(wrapper).prop('aria-expanded'));
    assert.equal(highlightedText(wrapper), '3:00 AM');
  });

  it('highlights the suggestion matching the current text when opening', () => {
    const wrapper = createComponent('3:00 pm');

    clickInput(wrapper);

    assert.equal(highlightedText(wrapper), '3:00 PM');
  });

  it('moves the highlight with the arrow keys, skipping disabled options', () => {
    const wrapper = createComponent();
    clickInput(wrapper);
    assert.equal(highlightedText(wrapper), '3:00 AM');

    // Down skips the disabled "3:30 AM" and stops at the end of the list.
    pressKey(wrapper, 'ArrowDown');
    assert.equal(highlightedText(wrapper), '3:00 PM');
    pressKey(wrapper, 'ArrowDown');
    assert.equal(highlightedText(wrapper), '3:00 PM');

    // Up skips it likewise and stops at the start.
    pressKey(wrapper, 'ArrowUp');
    assert.equal(highlightedText(wrapper), '3:00 AM');
    pressKey(wrapper, 'ArrowUp');
    assert.equal(highlightedText(wrapper), '3:00 AM');
  });

  it('follows the mouse with the highlight, except over disabled options', () => {
    const wrapper = createComponent();
    clickInput(wrapper);

    act(() => listOptions(wrapper).at(2).props().onMouseMove());
    wrapper.update();
    assert.equal(highlightedText(wrapper), '3:00 PM');

    act(() => listOptions(wrapper).at(1).props().onMouseMove());
    wrapper.update();
    assert.equal(highlightedText(wrapper), '3:00 PM');
  });

  it('chooses the highlighted suggestion with Enter', () => {
    const wrapper = createComponent();
    pressKey(wrapper, 'ArrowDown');

    const event = pressKey(wrapper, 'Enter');

    assert.calledWith(fakeOnChange, '3:00 AM');
    assert.called(fakeOnCommit);
    assert.isFalse(input(wrapper).prop('aria-expanded'));
    // The keypress meant "choose", not "submit the surrounding form".
    assert.isTrue(event.defaultPrevented);
  });

  it('commits the typed text with Enter when nothing is highlighted', () => {
    const wrapper = createComponent();
    typeText(wrapper, '9:99');

    const event = pressKey(wrapper, 'Enter');

    assert.called(fakeOnCommit);
    assert.isFalse(event.defaultPrevented);
  });

  it('closes without committing on Escape', () => {
    const wrapper = createComponent();
    clickInput(wrapper);

    pressKey(wrapper, 'Escape');

    assert.isFalse(input(wrapper).prop('aria-expanded'));
    assert.notCalled(fakeOnCommit);
  });

  it('commits when focus leaves the field', () => {
    const wrapper = createComponent();
    clickInput(wrapper);

    blurInput(wrapper);

    assert.called(fakeOnCommit);
    assert.isFalse(input(wrapper).prop('aria-expanded'));
  });

  it('keeps focus on the input while pressing on the dropdown', () => {
    const wrapper = createComponent();
    clickInput(wrapper);

    const event = new MouseEvent('mousedown', { cancelable: true });
    act(() => wrapper.find('ul').props().onMouseDown(event));

    // A default-allowed mousedown would move focus off the input and fire
    // its blur-commit before the option's click could land.
    assert.isTrue(event.defaultPrevented);
  });

  it('does not commit when focus moves into the dropdown', () => {
    const wrapper = createComponent();
    clickInput(wrapper);

    blurInput(wrapper, wrapper.find('ul').getDOMNode());

    assert.notCalled(fakeOnCommit);
    assert.isTrue(input(wrapper).prop('aria-expanded'));
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      // The field expects its label from the surrounding form, tied via
      // `inputId` — as `DueDateSelector` does.
      content: () =>
        mount(
          <div>
            <label htmlFor="a11y-time">Time</label>
            <TimeInput
              value=""
              onChange={fakeOnChange}
              options={defaultOptions}
              inputId="a11y-time"
            />
          </div>,
          { connected: true },
        ),
    }),
  );
});
