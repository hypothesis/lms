import { createElement } from 'preact';
import { mount } from 'enzyme';

import StudentSelector, { $imports } from '../StudentSelector';
import { checkAccessibility } from '../../../test-util/accessibility';
import mockImportedComponents from '../../../test-util/mock-imported-components';

describe('StudentSelector', () => {
  const renderSelector = (props = {}) => {
    const fakeOnSelectStudent = sinon.stub();
    const fakeSelectedStudentIndex = 0;
    const fakeStudents = [
      {
        username: 'student1',
        displayName: 'Student 1',
      },
      {
        username: 'student2',
        displayName: 'Student 2',
      },
    ];

    return mount(
      <StudentSelector
        onSelectStudent={fakeOnSelectStudent}
        selectedStudentIndex={fakeSelectedStudentIndex}
        students={fakeStudents}
        {...props}
      />
    );
  };

  beforeEach(() => {
    $imports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('shall have "All Students" as the default option', () => {
    const wrapper = renderSelector({ selectedStudentIndex: -1 });
    assert.equal(wrapper.find('select [selected=true]').text(), 'All Students');
  });

  it('sets the selected option to the second student when the student index is 1', () => {
    const wrapper = renderSelector({ selectedStudentIndex: 1 });
    assert.equal(wrapper.find('select [selected=true]').text(), 'Student 2');
  });

  it('calls the onSelectStudent callback when the select list is changed', () => {
    const onChange = sinon.spy();
    const wrapper = renderSelector({ onSelectStudent: onChange });
    wrapper.find('select').simulate('change');
    assert.isTrue(onChange.called);
  });

  it('calls onChange (with the next student index) when the next button is clicked', () => {
    const onChange = sinon.spy();
    const wrapper = renderSelector({ onSelectStudent: onChange });
    wrapper.find('IconButton button').last().simulate('click');
    assert.isTrue(onChange.calledWith(1));
  });

  it('calls onChange (with the previous student index) when the previous button is clicked', () => {
    const onChange = sinon.spy();
    const wrapper = renderSelector({
      onSelectStudent: onChange,
      selectedStudentIndex: 1,
    });
    wrapper.find('IconButton button').first().simulate('click');
    assert.isTrue(onChange.calledWith(0));
  });

  it('should disable the previous button when there are no previous options in the list', () => {
    const wrapper = renderSelector({ selectedStudentIndex: -1 });
    assert.isTrue(wrapper.find('IconButton').first().prop('disabled'));
  });

  it('should disable the next button when there are no next options in the list', () => {
    const wrapper = renderSelector({ selectedStudentIndex: 1 });
    assert.isTrue(wrapper.find('IconButton').last().prop('disabled'));
  });

  it.skip(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderSelector(),
    })
  );
});
