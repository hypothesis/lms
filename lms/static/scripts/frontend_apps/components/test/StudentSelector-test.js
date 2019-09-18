import { createElement } from 'preact';
import { shallow } from 'enzyme';

import StudentSelector from '../StudentSelector';

describe('StudentSelector', () => {
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
      <StudentSelector
        onSelectStudent={fakeOnSelectStudent}
        selectedStudentIndex={fakeSelectedStudentIndex}
        students={fakeStudents}
        {...props}
      />
    );
  };

  it('shall not have an initial selected option', () => {
    const wrapper = renderSelector({ selectedStudentIndex: -1 });
    assert.equal(
      wrapper.find('select [selected=true]').text(),
      'Select a student'
    );
  });

  it('sets the selected option should to the second user', () => {
    const wrapper = renderSelector({ selectedStudentIndex: 1 });
    assert.equal(wrapper.find('select [selected=true]').text(), 'User 2');
  });

  it('calls the onSelectStudent callback when the select list is changed', () => {
    const onChange = sinon.spy();
    const wrapper = renderSelector({ onSelectStudent: onChange });
    wrapper.find('select').simulate('change');
    assert.isTrue(onChange.called);
  });

  it('calls the callback with the next student index', () => {
    const onChange = sinon.spy();
    const wrapper = renderSelector({ onSelectStudent: onChange });
    wrapper
      .find('button')
      .last()
      .simulate('click');
    assert.isTrue(onChange.calledWith(1));
  });

  it('calls the callback with the next student index when clicking the previous button', () => {
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

  it('should not trigger the callback when clicking the previous button when there are no previous students', () => {
    const onChange = sinon.spy();
    const wrapper = renderSelector({ onSelectStudent: onChange });
    wrapper
      .find('button')
      .first()
      .simulate('click');
    assert.isFalse(onChange.called);
  });

  it('should not trigger the callback when clicking the next button when there are no next students', () => {
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
