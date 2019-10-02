import { createElement } from 'preact';
import { mount } from 'enzyme';
import LMSGrader from '../LMSGrader';

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
  const fakeOnChange = sinon.stub();

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
});
