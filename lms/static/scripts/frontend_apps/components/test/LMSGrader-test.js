import { act } from 'preact/test-utils';
import { Fragment, createElement } from 'preact';
import { mount } from 'enzyme';
import LMSGrader, { $imports } from '../LMSGrader';

describe('LMSGrader', () => {
  const fakeStudents = [
    {
      userid: 'user1',
      displayName: 'User 1',
    },
    {
      userid: 'user2',
      displayName: 'User 2',
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

  it('does not set a focus user by default', () => {
    renderGrader();
    sinon.assert.calledWith(fakeRemoveClientConfig, sinon.match(['focus']));
  });

  it('does not set a focus when the user index is invalid', () => {
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
