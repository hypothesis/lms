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
      userid: 'student1',
      displayName: 'Student 2',
      LISResultSourcedId: 2,
      LISOutcomeServiceUrl: '',
    },
  ];
  const fakeUpdateClientConfig = sinon.spy();
  const fakeRemoveClientConfig = sinon.spy();
  const fakeOnChange = sinon.stub();
  let fakeApiCall = sinon.stub();

  // eslint-disable-next-line react/prop-types
  const FakeStudentSelector = ({ children }) => {
    return <Fragment>{children}</Fragment>;
  };

  // eslint-disable-next-line react/prop-types
  const FakeSubmitGradeForm = ({ children }) => {
    return <Fragment>{children}</Fragment>;
  };

  // eslint-disable-next-line react/prop-types
  const FakeErrorDialog = ({ children }) => {
    return <Fragment>{children}</Fragment>;
  };

  beforeEach(() => {
    fakeApiCall = sinon.stub().resolves([]);
    $imports.$mock({
      '../utils/update-client-config': {
        updateClientConfig: fakeUpdateClientConfig,
        removeClientConfig: fakeRemoveClientConfig,
      },
      './ErrorDialog': FakeErrorDialog,
      './StudentSelector': FakeStudentSelector,
      './SubmitGradeForm': FakeSubmitGradeForm,
      '../utils/api': {
        apiCall: fakeApiCall,
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
        {...props}
      />
    );
  };

  it('creates a valid component with 2 students', () => {
    const wrapper = renderGrader();
    assert.equal(wrapper.text(), '2 Students');
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
    assert.equal(wrapper.text(), 'Student 2 of 2');
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

  describe('api requests', () => {
    it('shows the loading spinner when submitting a grade to apiCall', () => {
      const wrapper = renderGrader();
      act(() => {
        wrapper
          .find(FakeStudentSelector)
          .props()
          .onSelectStudent(0);
      });
      wrapper.update();

      act(() => {
        wrapper
          .find(FakeSubmitGradeForm)
          .props()
          .onSubmitGrade(1);
      });
      wrapper.update();
      assert.isTrue(wrapper.find('.LMSGrader__spinner').exists());
    });

    it('shows the error dialog when apiCall throws an error', () => {
      const wrapper = renderGrader();
      fakeApiCall.throws({ errorMessage: '' });
      act(() => {
        wrapper
          .find(FakeStudentSelector)
          .props()
          .onSelectStudent(0);
      });
      wrapper.update();
      act(() => {
        wrapper
          .find(FakeSubmitGradeForm)
          .props()
          .onSubmitGrade(1);
      });
      wrapper.update();
      assert.isTrue(wrapper.find(FakeErrorDialog).exists());
    });

    it('sets the gradeSaved prop to `true` when the apiCall resolves', async () => {
      const wrapper = renderGrader();
      act(() => {
        wrapper
          .find(FakeStudentSelector)
          .props()
          .onSelectStudent(0);
      });
      wrapper.update();
      act(() => {
        wrapper
          .find(FakeSubmitGradeForm)
          .props()
          .onSubmitGrade(1);
      });
      await fakeApiCall.resolves();
      wrapper.update();
      assert.isTrue(wrapper.find(FakeSubmitGradeForm).props().gradeSaved);
    });
  });
});
