import { act } from 'preact/test-utils';
import { Fragment, createElement } from 'preact';
import { mount } from 'enzyme';

import LMSGrader, { $imports } from '../LMSGrader';
import { checkAccessibility } from '../../../test-util/accessibility';

describe('LMSGrader', () => {
  let fakeStudents;
  let fakeOnChange;
  let fakeRpcCall;
  const fakeSidebarWindow = sinon.stub().resolves({
    frame: 'fake window',
    origin: 'fake origin',
  });

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
    fakeRpcCall = sinon.spy();
    $imports.$mock({
      './StudentSelector': FakeStudentSelector,
      '../../postmessage_json_rpc/client': {
        call: fakeRpcCall,
      },
      '../../postmessage_json_rpc/server': {
        getSidebarWindow: fakeSidebarWindow,
      },
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

  it('orders the students by last name (if it exists), then first name', () => {
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

  it('updates the order if the `students` change', () => {
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

  it('sorts an undefined displayName first', () => {
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

  it('set the selected student count to "Student 2 of 2" when the index changers to 1', async () => {
    const wrapper = renderGrader();
    act(() => {
      wrapper.find(FakeStudentSelector).props().onSelectStudent(1); // second student
    });
    assert.equal(
      wrapper.find('.LMSGrader__student-count').text(),
      'Student 2 of 2'
    );
  });

  it('does not set a focus user by default', async () => {
    renderGrader();
    await fakeSidebarWindow;
    assert.isTrue(
      fakeRpcCall.calledOnceWithExactly(
        'fake window',
        'fake origin',
        'changeFocusModeUser',
        [
          {
            username: undefined,
            displayName: undefined,
          },
        ]
      )
    );
  });
  it('sets the focused user when a valid index is passed', async () => {
    const wrapper = renderGrader();

    act(() => {
      wrapper.find(FakeStudentSelector).props().onSelectStudent(0); // note: initial index is -1
    });

    await fakeSidebarWindow;

    assert.isTrue(
      fakeRpcCall.secondCall.calledWithExactly(
        'fake window',
        'fake origin',
        'changeFocusModeUser',
        [
          {
            username: fakeStudents[0].userid,
            displayName: fakeStudents[0].displayName,
          },
        ]
      )
    );
  });

  it('does not set a focus user when the user index is invalid', async () => {
    const wrapper = renderGrader();
    act(() => {
      wrapper.find(FakeStudentSelector).props().onSelectStudent(-1); // invalid choice
    });

    await fakeSidebarWindow;

    assert.isTrue(
      fakeRpcCall.calledOnceWithExactly(
        'fake window',
        'fake origin',
        'changeFocusModeUser',
        [
          {
            username: undefined,
            displayName: undefined,
          },
        ]
      )
    );
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => renderGrader(),
    })
  );
});
