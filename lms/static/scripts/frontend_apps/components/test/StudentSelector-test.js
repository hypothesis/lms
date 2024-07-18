import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

import StudentSelector, { $imports } from '../StudentSelector';

describe('StudentSelector', () => {
  let fakeStudents;
  let wrappers;

  const renderSelector = (props = {}) => {
    const fakeOnSelectStudent = sinon.stub();
    const fakeSelectedStudentIndex = 0;

    const wrapper = mount(
      <StudentSelector
        onSelectStudent={fakeOnSelectStudent}
        selectedStudentIndex={fakeSelectedStudentIndex}
        students={fakeStudents}
        {...props}
      />,
    );
    wrappers.push(wrapper);

    return wrapper;
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
    wrappers = [];
  });

  afterEach(() => {
    $imports.$restore();
    wrappers.forEach(w => w.unmount());
  });

  it('shall have "All Students" as the default option', () => {
    const wrapper = renderSelector({ selectedStudent: null });
    assert.equal(wrapper.find('Select').prop('buttonContent'), 'All Students');
    assert.equal(
      wrapper.find('[data-testid="student-selector-label"]').text(),
      '2 Students',
    );
  });

  it('sets the selected option to the reflect the selected student', () => {
    const wrapper = renderSelector({ selectedStudent: fakeStudents[1] });
    assert.equal(wrapper.find('Select').prop('buttonContent'), 'Student 2');
    assert.equal(
      wrapper.find('[data-testid="student-selector-label"]').text(),
      'Student 2 of 2',
    );
  });

  it('calls the onSelectStudent callback when the select list is changed', () => {
    const onChange = sinon.spy();
    const wrapper = renderSelector({
      onSelectStudent: onChange,
      selectedStudent: fakeStudents[0],
    });
    wrapper.find('Select').props().onChange(fakeStudents[1]);
    assert.calledWith(onChange, fakeStudents[1]);
  });

  it('unsets the selected user when the "All Students" option is selected', () => {
    const onChange = sinon.spy();
    const wrapper = renderSelector({
      onSelectStudent: onChange,
      selectedStudent: fakeStudents[0],
    });
    // No student is selected
    wrapper.find('Select').props().onChange(null);
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
        .prop('disabled'),
    );
  });

  it('should disable the next button when there are no next options in the list', () => {
    const wrapper = renderSelector({ selectedStudent: fakeStudents[1] });
    assert.isTrue(wrapper.find('button').last().prop('disabled'));
  });

  it(
    'should pass a11y checks',
    checkAccessibility({ content: () => renderSelector() }),
  );
});
