import { RadioGroup } from '@hypothesis/frontend-shared';
import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import AssignmentTypeSelector from '../AssignmentTypeSelector';

describe('AssignmentTypeSelector', () => {
  let fakeOnChange;

  beforeEach(() => {
    fakeOnChange = sinon.stub();
  });

  function createComponent(
    selected = 'reading',
    types = ['reading', 'hide_and_reveal'],
  ) {
    return mount(
      <AssignmentTypeSelector
        types={types}
        selected={selected}
        onChange={fakeOnChange}
      />,
    );
  }

  it('reflects the selected assignment type', () => {
    const wrapper = createComponent('hide_and_reveal');
    assert.equal(
      wrapper.find('RadioGroup').prop('selected'),
      'hide_and_reveal',
    );
  });

  it('renders a radio option for each available type', () => {
    const wrapper = createComponent('reading', ['reading', 'hide_and_reveal']);
    const values = wrapper
      .find(RadioGroup.Radio)
      .map(radio => radio.prop('value'));
    assert.deepEqual(values, ['reading', 'hide_and_reveal']);
  });

  it('only renders the available types', () => {
    const wrapper = createComponent('reading', ['reading']);
    const values = wrapper
      .find(RadioGroup.Radio)
      .map(radio => radio.prop('value'));
    assert.deepEqual(values, ['reading']);
  });

  it('invokes onChange when a different type is selected', () => {
    const wrapper = createComponent('reading');

    act(() => wrapper.find('RadioGroup').props().onChange('hide_and_reveal'));

    assert.calledWith(fakeOnChange, 'hide_and_reveal');
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
