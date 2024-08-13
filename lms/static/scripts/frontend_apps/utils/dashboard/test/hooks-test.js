import { mount } from 'enzyme';

import { useDashboardFilters } from '../hooks';

describe('useDashboardFilters', () => {
  function FakeComponent() {
    const { filters, updateFilters, urlWithFilters } = useDashboardFilters();

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

        <div data-testid="url-with-filters">
          {urlWithFilters(filters, { path: '/hello/world' })}
        </div>
      </div>
    );
  }

  function setCurrentURL(url) {
    history.replaceState(null, '', url);
  }

  beforeEach(() => {
    // Reset query string
    setCurrentURL('?');
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

  function getURLWithFilters(wrapper) {
    return wrapper.find('[data-testid="url-with-filters"]').text();
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
        setCurrentURL(initialQueryString);

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
    setCurrentURL('?foo=bar&something=else');

    const wrapper = createComponent();
    wrapper.find('[data-testid="update-courses"]').simulate('click');

    assert.equal(
      '?foo=bar&something=else&course_id=111&course_id=222&course_id=333',
      location.search,
    );
  });

  it('preserves path', () => {
    setCurrentURL('/foo/bar');

    const wrapper = createComponent();
    wrapper.find('[data-testid="update-courses"]').simulate('click');

    assert.equal('?course_id=111&course_id=222&course_id=333', location.search);
    assert.equal('/foo/bar', location.pathname);
  });

  [
    {
      buttonId: 'update-courses',
      expectedURL: '/hello/world?course_id=111&course_id=222&course_id=333',
    },
    {
      buttonId: 'update-assignments',
      expectedURL:
        '/hello/world?assignment_id=123&assignment_id=456&assignment_id=789',
    },
    {
      buttonId: 'update-students',
      expectedURL: '/hello/world?student_id=abc&student_id=def',
    },
  ].forEach(({ buttonId, expectedURL }) => {
    it('builds URLs with filters', () => {
      // Current URL should be ignored
      setCurrentURL('/foo/bar');

      const wrapper = createComponent();

      assert.equal(getURLWithFilters(wrapper), '/hello/world');

      wrapper.find(`[data-testid="${buttonId}"]`).simulate('click');
      assert.equal(getURLWithFilters(wrapper), expectedURL);
    });
  });
});
