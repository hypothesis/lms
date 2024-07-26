import { mount } from 'enzyme';

import { useDashboardFilters } from '../hooks';

describe('useDashboardFilters', () => {
  function FakeComponent() {
    const { filters, updateFilters } = useDashboardFilters();

    return (
      <div>
        <div data-testid="course-ids">{filters.courseIds.join(',')}</div>
        <div data-testid="assignment-ids">
          {filters.assignmentIds.join(',')}
        </div>
        <div data-testid="student-ids">{filters.studentIds.join(',')}</div>

        <button
          onClick={() => updateFilters({ courseIds: ['111', '222', '333'] })}
          data-testid="update-courses"
        >
          Update courses
        </button>
        <button
          onClick={() =>
            updateFilters({ assignmentIds: ['123', '456', '789'] })
          }
          data-testid="update-assignments"
        >
          Update assignments
        </button>
        <button
          onClick={() => updateFilters({ studentIds: ['abc', 'def'] })}
          data-testid="update-students"
        >
          Update students
        </button>
      </div>
    );
  }

  function setQueryString(queryString) {
    history.replaceState(null, '', queryString);
  }

  beforeEach(() => {
    // Reset query string
    setQueryString('?');
  });

  function createComponent() {
    return mount(<FakeComponent />);
  }

  function getCurrentCourses(wrapper) {
    return wrapper.find('[data-testid="course-ids"]').text();
  }

  function getCurrentAssignments(wrapper) {
    return wrapper.find('[data-testid="assignment-ids"]').text();
  }

  function getCurrentStudents(wrapper) {
    return wrapper.find('[data-testid="student-ids"]').text();
  }

  [
    {
      initialQueryString: '?course_id=1&assignment_id=2',
      expectedCourses: '1',
      expectedAssignments: '2',
      expectedStudents: '',
    },
    {
      initialQueryString: '?course_id=1&course_id=2',
      expectedCourses: '1,2',
      expectedAssignments: '',
      expectedStudents: '',
    },
    {
      initialQueryString: '?student_id=abc&student_id=def&assignment_id=3',
      expectedCourses: '',
      expectedAssignments: '3',
      expectedStudents: 'abc,def',
    },
    {
      initialQueryString: '?student_id=abc',
      expectedCourses: '',
      expectedAssignments: '',
      expectedStudents: 'abc',
    },
  ].forEach(
    ({
      initialQueryString,
      expectedCourses,
      expectedAssignments,
      expectedStudents,
    }) => {
      it('reads params from the query', () => {
        setQueryString(initialQueryString);

        const wrapper = createComponent();

        assert.equal(getCurrentCourses(wrapper), expectedCourses);
        assert.equal(getCurrentAssignments(wrapper), expectedAssignments);
        assert.equal(getCurrentStudents(wrapper), expectedStudents);
      });
    },
  );

  [
    {
      buttonId: 'update-courses',
      getResult: getCurrentCourses,
      expectedResult: '111,222,333',
      expectedQueryString: '?course_id=111&course_id=222&course_id=333',
    },
    {
      buttonId: 'update-assignments',
      getResult: getCurrentAssignments,
      expectedResult: '123,456,789',
      expectedQueryString:
        '?assignment_id=123&assignment_id=456&assignment_id=789',
    },
    {
      buttonId: 'update-students',
      getResult: getCurrentStudents,
      expectedResult: 'abc,def',
      expectedQueryString: '?student_id=abc&student_id=def',
    },
  ].forEach(({ buttonId, getResult, expectedResult, expectedQueryString }) => {
    it('persists updated values in query string', () => {
      const wrapper = createComponent();

      wrapper.find(`[data-testid="${buttonId}"]`).simulate('click');

      assert.equal(getResult(wrapper), expectedResult);
      assert.equal(location.search, expectedQueryString);
    });
  });

  it('preserves unknown query params', () => {
    setQueryString('?foo=bar&something=else');

    const wrapper = createComponent();
    wrapper.find('[data-testid="update-courses"]').simulate('click');

    assert.equal(
      '?foo=bar&something=else&course_id=111&course_id=222&course_id=333',
      location.search,
    );
  });
});
