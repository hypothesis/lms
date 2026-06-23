import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import CheckpointSelector from '../CheckpointSelector';

describe('CheckpointSelector', () => {
  let fakeOnChange;

  beforeEach(() => {
    fakeOnChange = sinon.stub();
  });

  function createComponent(selected = 'manual') {
    return mount(
      <CheckpointSelector selected={selected} onChange={fakeOnChange} />,
    );
  }

  it('reflects the selected checkpoint type', () => {
    const wrapper = createComponent('manual');
    assert.equal(wrapper.find('RadioGroup').prop('selected'), 'manual');
  });

  it('invokes onChange when "manual" is selected', () => {
    const wrapper = createComponent();

    act(() => wrapper.find('RadioGroup').props().onChange('manual'));

    assert.calledWith(fakeOnChange, 'manual');
  });

  it('ignores selection of not-yet-available options', () => {
    const wrapper = createComponent();

    act(() => wrapper.find('RadioGroup').props().onChange('more'));

    assert.notCalled(fakeOnChange);
  });

  it('passes through any real (non-placeholder) checkpoint type', () => {
    const wrapper = createComponent();

    // A future CheckpointType (anything other than the "more" placeholder)
    // should propagate without changing the guard.
    act(() => wrapper.find('RadioGroup').props().onChange('automatic'));

    assert.calledWith(fakeOnChange, 'automatic');
  });

  it('shows the reveal note when "manual" is selected', () => {
    const wrapper = createComponent('manual');

    assert.include(
      wrapper.text(),
      'Students will see when the settings have changed',
    );
  });

  it('hides the reveal note when a non-manual option is selected', () => {
    // `selected` is typed `'manual'` today (the only option), so this exercises
    // the conditional that will matter once more checkpoint types exist.
    const wrapper = createComponent('more');

    assert.notInclude(
      wrapper.text(),
      'Students will see when the settings have changed',
    );
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
