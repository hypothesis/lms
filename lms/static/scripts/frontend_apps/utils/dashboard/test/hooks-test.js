import { mount } from 'enzyme';

import { useDashboardFilters, $imports } from '../hooks';

describe('useDashboardFilters', () => {
  let fakeUseLocation;
  let fakeUseSearch;
  let fakeNavigate;

  function FakeComponent() {
    const { filters, updateFilters, urlWithFilters } = useDashboardFilters();

    return (
      <div>
        <div data-testid="course-ids">{filters.courseIds.join(',')}</div>
        <div data-testid="assignment-ids">
          {filters.assignmentIds.join(',')}
        </div>
        <div data-testid="student-ids">{filters.studentIds.join(',')}</div>
        <div data-testid="segment-ids">{filters.segmentIds.join(',')}</div>

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
        <button
          onClick={() => updateFilters({ segmentIds: ['foo', 'bar'] })}
          data-testid="update-segments"
        >
          Update segments
        </button>

        <div data-testid="url-with-filters">
          {urlWithFilters(filters, { path: '/hello/world' })}
        </div>
      </div>
    );
  }

  beforeEach(() => {
    fakeUseSearch = sinon.stub().returns('');
    fakeNavigate = sinon.stub();
    fakeUseLocation = sinon.stub().returns(['', fakeNavigate]);

    $imports.$mock({
      'wouter-preact': {
        useSearch: fakeUseSearch,
        useLocation: fakeUseLocation,
      },
    });
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

  function getCurrentSegments(wrapper) {
    return wrapper.find('[data-testid="segment-ids"]').text();
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
      expectedSegments: '',
    },
    {
      initialQueryString: '?course_id=1&course_id=2',
      expectedCourses: '1,2',
      expectedAssignments: '',
      expectedStudents: '',
      expectedSegments: '',
    },
    {
      initialQueryString: '?student_id=abc&student_id=def&assignment_id=3',
      expectedCourses: '',
      expectedAssignments: '3',
      expectedStudents: 'abc,def',
      expectedSegments: '',
    },
    {
      initialQueryString: '?student_id=abc',
      expectedCourses: '',
      expectedAssignments: '',
      expectedStudents: 'abc',
      expectedSegments: '',
    },
    {
      initialQueryString: '?segment_id=bar&segment_id=baz&student_id=abc',
      expectedCourses: '',
      expectedAssignments: '',
      expectedStudents: 'abc',
      expectedSegments: 'bar,baz',
    },
  ].forEach(
    ({
      initialQueryString,
      expectedCourses,
      expectedAssignments,
      expectedStudents,
      expectedSegments,
    }) => {
      it('reads params from the query', () => {
        fakeUseSearch.returns(initialQueryString);

        const wrapper = createComponent();

        assert.equal(getCurrentCourses(wrapper), expectedCourses);
        assert.equal(getCurrentAssignments(wrapper), expectedAssignments);
        assert.equal(getCurrentStudents(wrapper), expectedStudents);
        assert.equal(getCurrentSegments(wrapper), expectedSegments);
      });
    },
  );

  [
    {
      buttonId: 'update-courses',
      expectedQueryString: '?course_id=111&course_id=222&course_id=333',
    },
    {
      buttonId: 'update-assignments',
      expectedQueryString:
        '?assignment_id=123&assignment_id=456&assignment_id=789',
    },
    {
      buttonId: 'update-students',
      expectedQueryString: '?student_id=abc&student_id=def',
    },
    {
      buttonId: 'update-segments',
      expectedQueryString: '?segment_id=foo&segment_id=bar',
    },
  ].forEach(({ buttonId, expectedQueryString }) => {
    it('persists updated values in query string', () => {
      const wrapper = createComponent();

      wrapper.find(`[data-testid="${buttonId}"]`).simulate('click');

      assert.calledWith(fakeNavigate, expectedQueryString);
    });
  });

  it('preserves unknown query params', () => {
    fakeUseSearch.returns('?foo=bar&something=else');

    const wrapper = createComponent();
    wrapper.find('[data-testid="update-courses"]').simulate('click');

    assert.calledWith(
      fakeNavigate,
      '?foo=bar&something=else&course_id=111&course_id=222&course_id=333',
    );
  });

  it('preserves path', () => {
    fakeUseLocation.returns(['/foo/bar', fakeNavigate]);

    const wrapper = createComponent();
    wrapper.find('[data-testid="update-courses"]').simulate('click');

    assert.calledWith(
      fakeNavigate,
      '/foo/bar?course_id=111&course_id=222&course_id=333',
    );
  });

  it('ignores current path when one is provided', () => {
    // Current URL should be ignored
    fakeUseLocation.returns(['/foo/bar', fakeNavigate]);

    const wrapper = createComponent();

    assert.equal(getURLWithFilters(wrapper), '/hello/world');
  });
});
