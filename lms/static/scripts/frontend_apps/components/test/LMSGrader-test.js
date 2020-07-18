import { act } from 'preact/test-utils';
import { Fragment, createElement } from 'preact';
import { mount } from 'enzyme';

import LMSGrader, { $imports } from '../LMSGrader';
import { checkAccessibility } from '../../../test-util/accessibility';

describe('LMSGrader', () => {
  let fakeStudents;
  let fakeOnChange;
  let fakeClientRpc;

  // eslint-disable-next-line react/prop-types
  const FakeStudentSelector = ({ children }) => {
    return <Fragment>{children}</Fragment>;
  };

  /**
   * Helper to return a list of displayNames of the students.
   *
   * @param {import("enzyme").CommonWrapper} wrapper - Enzyme wrapper
   * @returns {Array<string>}
   */
  function getDisplayNames(wrapper) {
    return wrapper
      .find('FakeStudentSelector')
      .prop('students')
      .map(s => {
        return s.displayName;
      });
  }

  beforeEach(() => {
    fakeStudents = [
      {
        userid: 'acct:student1@authority',
        displayName: 'Student 1',
        LISResultSourcedId: 1,
        LISOutcomeServiceUrl: '',
      },
      {
        userid: 'acct:student2@authority',
        displayName: 'Student 2',
        LISResultSourcedId: 2,
        LISOutcomeServiceUrl: '',
      },
    ];
    fakeOnChange = sinon.spy();
    fakeClientRpc = {
      setFocusedUser: sinon.stub(),
    };

    $imports.$mock({
      './StudentSelector': FakeStudentSelector,
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  const renderGrader = (props = {}) => {
    return mount(
      <LMSGrader
        onChangeSelectedUser={fakeOnChange}
        students={fakeStudents}
        courseName={'course name'}
        assignmentName={'course assignment'}
        clientRpc={fakeClientRpc}
        {...props}
      >
        <div title="The assignment content iframe" />
      </LMSGrader>
    );
  };

  it('sets the assignment and course names', () => {
    const wrapper = renderGrader();
    assert.equal(
      wrapper.find('.LMSGrader__assignment').text(),
      'course assignment'
    );
    assert.equal(wrapper.find('.LMSGrader__name').text(), 'course name');
  });

  it('creates a valid component with 2 students', () => {
    const wrapper = renderGrader();
    assert.equal(
      wrapper.find('.LMSGrader__student-count').text(),
      '2 Students'
    );
  });

  it('orders the students by displayName', () => {
    // Un-order students
    fakeStudents = [
      {
        displayName: 'Student Beta',
      },
      {
        displayName: 'Students Beta',
      },
      {
        displayName: 'Beta',
      },
      {
        displayName: 'student Beta',
      },
      {
        displayName: 'Student Delta',
      },
      {
        displayName: 'Student Alpha',
      },
      {
        displayName: 'Alpha',
      },
    ];
    const wrapper = renderGrader();
    const orderedStudentNames = getDisplayNames(wrapper);
    assert.match(
      [
        'Alpha',
        'Beta',
        'Student Alpha',
        'Student Beta',
        // 'student Beta' ties with 'Student Beta',
        // but since 'Student Beta' came first, it wins.
        'student Beta',
        'Student Delta',
        'Students Beta',
      ],
      orderedStudentNames
    );
  });

  it('updates the order if the `students` prop changes', () => {
    // Un-order students
    fakeStudents = [
      {
        displayName: 'Beta',
      },
      {
        displayName: 'Alpha',
      },
    ];
    const wrapper = renderGrader();
    let orderedStudentNames = getDisplayNames(wrapper);
    assert.match(['Alpha', 'Beta'], orderedStudentNames);
    // New list of students
    wrapper.setProps({
      students: [
        {
          displayName: 'Beta',
        },
        {
          displayName: 'Gamma',
        },
      ],
    });
    orderedStudentNames = getDisplayNames(wrapper);
    assert.match(['Beta', 'Gamma'], orderedStudentNames);
  });

  it('puts students with empty displayNames at the beginning of sorted students', () => {
    // Un-order students
    fakeStudents = [
      {
        displayName: 'Student Beta',
      },
      {
        displayName: undefined,
      },
    ];
    const wrapper = renderGrader();
    const orderedStudentNames = wrapper
      .find('FakeStudentSelector')
      .prop('students')
      .map(s => {
        return s.displayName;
      });
    assert.match([undefined, 'Student Beta'], orderedStudentNames);
  });

  it('set the selected student count to "Student 2 of 2" when the index changers to 1', () => {
    const wrapper = renderGrader();
    act(() => {
      wrapper.find(FakeStudentSelector).props().onSelectStudent(1); // second student
    });
    assert.equal(
      wrapper.find('.LMSGrader__student-count').text(),
      'Student 2 of 2'
    );
  });

  it('does not set a focus user by default', () => {
    renderGrader();
    assert.calledWith(fakeClientRpc.setFocusedUser, null);
  });

  it('sets the focused user when a valid index is passed', () => {
    const wrapper = renderGrader();

    act(() => {
      wrapper.find(FakeStudentSelector).props().onSelectStudent(0); // note: initial index is -1
    });

    assert.calledWith(fakeClientRpc.setFocusedUser, fakeStudents[0]);
  });

  it('does not set a focus user when the user index is invalid', () => {
    const wrapper = renderGrader();
    act(() => {
      wrapper.find(FakeStudentSelector).props().onSelectStudent(-1); // invalid choice
    });

    assert.calledWith(fakeClientRpc.setFocusedUser, null);
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderGrader(),
    })
  );
});
