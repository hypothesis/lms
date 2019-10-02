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

  // eslint-disable-next-line react/prop-types
  const FakeStudentSelector = ({ children }) => {
    return <Fragment>{children}</Fragment>;
  };

  beforeEach(() => {
    $imports.$mock({
      './StudentSelector': FakeStudentSelector,
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  const renderGrader = (props = {}) => {
    return mount(<LMSGrader students={fakeStudents} {...props} />);
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
});
