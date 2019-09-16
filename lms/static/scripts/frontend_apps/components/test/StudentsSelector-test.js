import { createElement } from 'preact';
import { shallow } from 'enzyme';

import StudentsSelector from '../StudentsSelector';

describe('StudentsSelector', () => {
  const renderSelector = (props = {}) => {
    const fakeOnSelectStudent = sinon.stub();
    const fakeSelectedStudentIndex = 0;
    const fakeStudents = [
      {
        username: 'user1',
        displayName: 'User 1',
      },
      {
        username: 'user2',
        displayName: 'User 2',
      },
    ];

    return shallow(
      <StudentsSelector
        onSelectStudent={fakeOnSelectStudent}
        selectedStudentIndex={fakeSelectedStudentIndex}
        students={fakeStudents}
        {...props}
      />
    );
  };

  it('the initial selected option should be the first user', () => {
    const wrapper = renderSelector();
    assert.equal(wrapper.find('select [selected=true]').text(), 'User 1');
  });

  it('the initial selected option should be the second user', () => {
    const wrapper = renderSelector({ selectedStudentIndex: 1 });
    assert.equal(wrapper.find('select [selected=true]').text(), 'User 2');
  });

  it('onSelectStudent callback should be called when the select list is changed', () => {
    const onChange = sinon.spy();
    const wrapper = renderSelector({ onSelectStudent: onChange });
    wrapper.find('select').simulate('change');
    assert.isTrue(onChange.called);
  });

  it('clicking the next button calls the callback with the next student index ', () => {
    const onChange = sinon.spy();
    const wrapper = renderSelector({ onSelectStudent: onChange });
    wrapper
      .find('button')
      .last()
      .simulate('click');
    assert.isTrue(onChange.calledWith(1));
  });

  it('clicking the previous button calls the callback with the next student index ', () => {
    const onChange = sinon.spy();
    const wrapper = renderSelector({
      onSelectStudent: onChange,
      selectedStudentIndex: 1,
    });
    wrapper
      .find('button')
      .first()
      .simulate('click');
    assert.isTrue(onChange.calledWith(0));
  });

  it('clicking the previous button when there are no previous students should not trigger the callback', () => {
    const onChange = sinon.spy();
    const wrapper = renderSelector({ onSelectStudent: onChange });
    wrapper
      .find('button')
      .first()
      .simulate('click');
    assert.isFalse(onChange.called);
  });

  it('clicking the next button when there are no next students should not trigger the callback', () => {
    const onChange = sinon.spy();
    const wrapper = renderSelector({
      onSelectStudent: onChange,
      selectedStudentIndex: 1,
    });
    wrapper
      .find('button')
      .last()
      .simulate('click');
    assert.isFalse(onChange.called);
  });
});
