import { act } from 'preact/test-utils';
import { Fragment, createElement } from 'preact';
import { mount } from 'enzyme';
import LMSGrader, { $imports } from '../LMSGrader';

describe('LMSGrader', () => {
  const fakeStudents = [
    {
      userid: 'student1',
      displayName: 'Student 1',
    },
    {
      userid: 'student1',
      displayName: 'Student 2',
    },
  ];
  const fakeUpdateClientConfig = sinon.spy();
  const fakeRemoveClientConfig = sinon.spy();
  const fakeOnChange = sinon.stub();

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
    $imports.$restore();
  });

  const renderGrader = (props = {}) => {
    return mount(
      <LMSGrader
        onChangeSelectedUser={fakeOnChange}
        students={fakeStudents}
        {...props}
      />
    );
  };

  it('creates a valid component with 2 students', () => {
    const wrapper = renderGrader();
    assert.equal(wrapper.text(), '2 students');
  });

  it('set the selected student count to "2/2" when the index changers to 1', () => {
    const wrapper = renderGrader();
    act(() => {
      wrapper
        .find(FakeStudentSelector)
        .props()
        .onSelectStudent(1); // second student
    });
    wrapper.update();
    assert.equal(wrapper.text(), '2/2');
  });

  it('passes a default value of "0" to onChangeSelectedUser when no a student is selected', () => {
    renderGrader();
    assert.isTrue(fakeOnChange.calledWithExactly('0'));
  });

  it('passes the unique userid to onChangeSelectedUser when a student is selected', () => {
    const wrapper = renderGrader();
    act(() => {
      wrapper
        .find(FakeStudentSelector)
        .props()
        .onSelectStudent(1); // second student
    });
    wrapper.update();
    assert.isTrue(fakeOnChange.calledWithExactly('student1'));
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
