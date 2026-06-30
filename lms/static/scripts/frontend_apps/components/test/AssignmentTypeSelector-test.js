import { checkAccessibility, mount } from '@hypothesis/frontend-testing';
import { act } from 'preact/test-utils';

import AssignmentTypeSelector from '../AssignmentTypeSelector';

describe('AssignmentTypeSelector', () => {
  let fakeOnSelect;

  beforeEach(() => {
    fakeOnSelect = sinon.stub();
  });

  function createComponent(types = ['reading', 'hide_and_reveal']) {
    return mount(
      <AssignmentTypeSelector types={types} onSelect={fakeOnSelect} />,
    );
  }

  function optionTestIds(wrapper) {
    return wrapper.find('Button').map(button => button.prop('data-testid'));
  }

  it('renders a button for each available type', () => {
    const wrapper = createComponent(['reading', 'hide_and_reveal']);
    assert.deepEqual(optionTestIds(wrapper), [
      'assignment-type-reading',
      'assignment-type-hide_and_reveal',
    ]);
  });

  it('only renders the available types', () => {
    const wrapper = createComponent(['reading']);
    assert.deepEqual(optionTestIds(wrapper), ['assignment-type-reading']);
  });

  it('falls back to the raw key for unknown types', () => {
    const wrapper = createComponent(['mystery']);
    assert.deepEqual(optionTestIds(wrapper), ['assignment-type-mystery']);
  });

  it('invokes onSelect when a type is clicked', () => {
    const wrapper = createComponent();

    act(() =>
      wrapper
        .find('Button[data-testid="assignment-type-hide_and_reveal"]')
        .props()
        .onClick(),
    );

    assert.calledWith(fakeOnSelect, 'hide_and_reveal');
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
