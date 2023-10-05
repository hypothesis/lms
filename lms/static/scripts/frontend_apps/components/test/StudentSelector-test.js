import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

import StudentSelector, { $imports } from '../StudentSelector';

describe('StudentSelector', () => {
  let fakeStudents;

  const renderSelector = (props = {}) => {
    const fakeOnSelectStudent = sinon.stub();
    const fakeSelectedStudentIndex = 0;

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
    fakeStudents = [
      {
        displayName: 'Student 1',
      },
      {
        displayName: 'Student 2',
      },
    ];
  });

  afterEach(() => {
    $imports.$restore();
  });

  it('shall have "All Students" as the default option', () => {
    const wrapper = renderSelector({ selectedStudent: null });
    assert.equal(wrapper.find('select [selected=true]').text(), 'All Students');
    assert.equal(
      wrapper.find('[data-testid="student-selector-label"]').text(),
      '2 Students'
    );
  });

  it('sets the selected option to the reflect the selected student', () => {
    const wrapper = renderSelector({ selectedStudent: fakeStudents[1] });
    assert.equal(wrapper.find('select [selected=true]').text(), 'Student 2');
    assert.equal(
      wrapper.find('[data-testid="student-selector-label"]').text(),
      'Student 2 of 2'
    );
  });

  it('calls the onSelectStudent callback when the select list is changed', () => {
    const onChange = sinon.spy();
    const wrapper = renderSelector({
      onSelectStudent: onChange,
      selectedStudent: fakeStudents[0],
    });
    wrapper.find('select').simulate('change');
    assert.isTrue(onChange.called);
  });

  it('unsets the selected user when the "All Students" option is selected', () => {
    const onChange = sinon.spy();
    const wrapper = renderSelector({
      // No student is selected
      onSelectStudent: onChange,
    });
    wrapper.find('select').simulate('change');
    assert.calledWith(onChange, null);
  });

  it('calls onChange (with the next student) when the next button is clicked', () => {
    const onChange = sinon.spy();
    const wrapper = renderSelector({ onSelectStudent: onChange });
    wrapper.find('button').last().simulate('click');
    assert.isTrue(onChange.calledWith(fakeStudents[0]));
  });

  it('calls onChange (with the previous student) when the previous button is clicked', () => {
    const onChange = sinon.spy();
    const wrapper = renderSelector({
      onSelectStudent: onChange,
      selectedStudent: fakeStudents[1],
    });
    wrapper
      .find('button[data-testid="previous-student-button"]')
      .simulate('click');
    assert.isTrue(onChange.calledWith(fakeStudents[0]));
  });

  it('sets selected student to `null` when the previous button clicked and no previous students', () => {
    const onChange = sinon.spy();
    const wrapper = renderSelector({
      onSelectStudent: onChange,
      selectedStudent: fakeStudents[0],
    });
    wrapper
      .find('button[data-testid="previous-student-button"]')
      .simulate('click');
    assert.isTrue(onChange.calledWith(null));
  });

  it('should disable the previous button when there are no previous options in the list', () => {
    const wrapper = renderSelector({ selectedStudent: null });
    assert.isTrue(
      wrapper
        .find('button[data-testid="previous-student-button"]')
        .prop('disabled')
    );
  });

  it('should disable the next button when there are no next options in the list', () => {
    const wrapper = renderSelector({ selectedStudent: fakeStudents[1] });
    assert.isTrue(wrapper.find('button').last().prop('disabled'));
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => renderSelector() })
  );
});
