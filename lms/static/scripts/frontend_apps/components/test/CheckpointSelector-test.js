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

  it('explains what a checkpoint is', () => {
    const wrapper = createComponent();

    assert.include(
      wrapper.text(),
      'A Checkpoint is the moment when student annotations switch from hidden to visible',
    );
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
