import { act } from 'preact/test-utils';
import { Fragment, createElement } from 'preact';
import { mount } from 'enzyme';
import LMSGrader, { $imports } from '../LMSGrader';

describe('LMSGrader', () => {
  const fakeStudents = [
    {
      userid: 'student1',
      displayName: 'Student 1',
      LISResultSourcedId: 1,
      LISOutcomeServiceUrl: '',
    },
    {
      userid: 'student2',
      displayName: 'Student 2',
      LISResultSourcedId: 2,
      LISOutcomeServiceUrl: '',
    },
  ];
  const fakeUpdateClientConfig = sinon.spy();
  const fakeRemoveClientConfig = sinon.spy();
  const fakeOnChange = sinon.spy();

  // eslint-disable-next-line react/prop-types
  const FakeStudentSelector = ({ children }) => {
    return <Fragment>{children}</Fragment>;
  };

  beforeEach(() => {
    $imports.$mock({
      '../utils/update-client-config': {
        updateClientConfig: fakeUpdateClientConfig,
        removeClientConfig: fakeRemoveClientConfig,
      },
      './StudentSelector': FakeStudentSelector,
    });
  });

  afterEach(() => {
    fakeUpdateClientConfig.resetHistory();
    fakeRemoveClientConfig.resetHistory();
    fakeOnChange.resetHistory();
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
      />
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

  it('set the selected student count to "Student 2 of 2" when the index changers to 1', () => {
    const wrapper = renderGrader();
    act(() => {
      wrapper
        .find(FakeStudentSelector)
        .props()
        .onSelectStudent(1); // second student
    });
    assert.equal(
      wrapper.find('.LMSGrader__student-count').text(),
      'Student 2 of 2'
    );
  });

  it('passes a default value of "{}" to onChangeSelectedUser when no a student is selected', () => {
    renderGrader();
    assert.isTrue(fakeOnChange.calledWithExactly({}));
  });

  it('passes the unique user object to onChangeSelectedUser when a student is selected', () => {
    const wrapper = renderGrader();
    act(() => {
      wrapper
        .find(FakeStudentSelector)
        .props()
        .onSelectStudent(1); // second student
    });

    assert.calledWith(fakeOnChange.secondCall, {
      userid: 'student2',
      displayName: 'Student 2',
      LISResultSourcedId: 2,
      LISOutcomeServiceUrl: '',
    });
  });

  it('does not set a focus user by default', () => {
    renderGrader();
    sinon.assert.calledWith(fakeRemoveClientConfig, sinon.match(['focus']));
  });

  it('does not set a focus user when the user index is invalid', () => {
    const wrapper = renderGrader();
    act(() => {
      wrapper
        .find(FakeStudentSelector)
        .props()
        .onSelectStudent(-2); // invalid choice
    });
    wrapper.update();

    sinon.assert.calledWith(fakeRemoveClientConfig, sinon.match(['focus']));
  });

  it('changes the sidebar config to focus to the specified user when onSelectStudent is called with a valid user index', () => {
    const wrapper = renderGrader();
    act(() => {
      wrapper
        .find(FakeStudentSelector)
        .props()
        .onSelectStudent(0); // initial index is -1
    });
    wrapper.update();

    sinon.assert.calledWith(
      fakeUpdateClientConfig,
      sinon.match({
        focus: {
          user: {
            username: fakeStudents[0].userid,
            displayName: fakeStudents[0].displayName,
          },
        },
      })
    );
  });
});
