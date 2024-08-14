import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import { act } from 'preact/test-utils';
import sinon from 'sinon';

import { Config } from '../../../config';
import CourseActivity, { $imports } from '../CourseActivity';

describe('CourseActivity', () => {
  const assignments = [
    {
      id: 2,
      title: 'b',
      annotation_metrics: {
        last_activity: '2020-01-01T00:00:00',
        annotations: 8,
        replies: 0,
      },
    },
    {
      id: 1,
      title: 'a',
      annotation_metrics: {
        last_activity: '2020-01-02T00:00:00',
        annotations: 3,
        replies: 20,
      },
    },
    {
      id: 3,
      title: 'c',
      annotation_metrics: {
        last_activity: '2020-01-02T00:00:00',
        annotations: 5,
        replies: 100,
      },
    },
  ];
  const activeCourse = { id: 123, title: 'The title' };

  let fakeUseAPIFetch;
  let fakeConfig;
  let fakeNavigate;
  let fakeUseSearch;
  let wrappers;

  function setCurrentURL(url) {
    history.replaceState(null, '', url);
  }

  beforeEach(() => {
    // Avoid filters set during one test to affect subsequent ones
    setCurrentURL('?');

    fakeUseAPIFetch = sinon.stub().callsFake(url => ({
      isLoading: false,
      data: url.endsWith('stats') ? { assignments } : activeCourse,
    }));
    fakeConfig = {
      dashboard: {
        routes: {
          course: '/api/dashboard/course/:course_id',
          course_assignments_metrics: '/api/dashboard/course/:course_id/stats',
        },
      },
    };
    fakeNavigate = sinon.stub();
    fakeUseSearch = sinon.stub().returns('current=query');
    wrappers = [];

    $imports.$mock(mockImportedComponents());
    $imports.$mock({
      '../../utils/api': {
        useAPIFetch: fakeUseAPIFetch,
      },
      'wouter-preact': {
        useParams: sinon.stub().returns({ courseId: '123' }),
        useSearch: fakeUseSearch,
        useLocation: sinon.stub().returns(['', fakeNavigate]),
      },
    });
  });

  afterEach(() => {
    wrappers.forEach(wrapper => wrapper.unmount());
    $imports.$restore();
  });

  function createComponent() {
    const wrapper = mount(
      <Config.Provider value={fakeConfig}>
        <CourseActivity />
      </Config.Provider>,
    );
    wrappers.push(wrapper);

    return wrapper;
  }

  /**
   * @param {'students' | 'assignments'} filterProp
   */
  function updateFilter(wrapper, filterProp, ids) {
    const filters = wrapper.find('DashboardActivityFilters');
    act(() => filters.prop(filterProp).onChange(ids));
    wrapper.update();
  }

  it('shows loading indicators while data is loading', () => {
    fakeUseAPIFetch.returns({ isLoading: true });

    const wrapper = createComponent();
    const titleElement = wrapper.find('[data-testid="title"]');
    const tableElement = wrapper.find('OrderableActivityTable');

    assert.equal(titleElement.text(), 'Loading...');
    assert.isTrue(tableElement.prop('loading'));
  });

  it('shows error if loading data fails', () => {
    fakeUseAPIFetch.returns({ error: new Error('Something failed') });

    const wrapper = createComponent();
    const titleElement = wrapper.find('[data-testid="title"]');
    const tableElement = wrapper.find('OrderableActivityTable');

    assert.equal(titleElement.text(), 'Could not load course title');
    assert.equal(
      tableElement.prop('emptyMessage'),
      'Could not load assignments',
    );
  });

  it('shows expected title', () => {
    const wrapper = createComponent();
    const titleElement = wrapper.find('[data-testid="title"]');
    const tableElement = wrapper.find('OrderableActivityTable');
    const expectedTitle = 'The title';

    assert.equal(titleElement.text(), expectedTitle);
    assert.equal(tableElement.prop('title'), expectedTitle);
  });

  it('shows empty assignments message', () => {
    const wrapper = createComponent();
    const tableElement = wrapper.find('OrderableActivityTable');

    assert.equal(tableElement.prop('emptyMessage'), 'No assignments found');
  });

  it('flattens assignments to table rows', () => {
    const wrapper = createComponent();
    const tableElement = wrapper.find('OrderableActivityTable');

    assert.deepEqual(tableElement.prop('rows'), [
      {
        id: 2,
        title: 'b',
        last_activity: '2020-01-01T00:00:00',
        annotations: 8,
        replies: 0,
      },
      {
        id: 1,
        title: 'a',
        last_activity: '2020-01-02T00:00:00',
        annotations: 3,
        replies: 20,
      },
      {
        id: 3,
        title: 'c',
        last_activity: '2020-01-02T00:00:00',
        annotations: 5,
        replies: 100,
      },
    ]);
  });

  [
    { fieldName: 'title', expectedValue: 'Frog dissection' },
    { fieldName: 'annotations', expectedValue: '37' },
    { fieldName: 'replies', expectedValue: '25' },
    {
      fieldName: 'last_activity',
      expectedValue: '2024-01-01T10:35:18',
    },
  ].forEach(({ fieldName, expectedValue }) => {
    it('renders every field as expected', () => {
      const assignmentStats = {
        id: 123,
        title: 'Frog dissection',
        last_activity: '2024-01-01T10:35:18',
        annotations: 37,
        replies: 25,
      };
      const wrapper = createComponent();

      const item = wrapper
        .find('OrderableActivityTable')
        .props()
        .renderItem(assignmentStats, fieldName);

      const itemWrapper = mount(item);

      if (fieldName === 'last_activity') {
        assert.equal(itemWrapper.prop('date'), expectedValue);
        return;
      }

      assert.equal(itemWrapper.text(), expectedValue);

      if (fieldName === 'title') {
        assert.equal(itemWrapper.prop('href'), '/assignments/123/');
      }
    });
  });

  context('when building row confirmation links', () => {
    function getLinkForId(wrapper, id) {
      return wrapper
        .find('OrderableActivityTable')
        .props()
        .navigateOnConfirmRow({ id });
    }

    [12, 35, 1, 500].forEach(assignmentId => {
      it('builds expected link for row confirmation', () => {
        const wrapper = createComponent();
        assert.equal(
          getLinkForId(wrapper, assignmentId),
          `/assignments/${assignmentId}/`,
        );
      });
    });

    [
      {
        prop: 'students',
        arg: ['123', '456'],
        expectedLink: '/assignments/123/?student_id=123&student_id=456',
      },
      {
        prop: 'assignments',
        arg: ['999'],
        expectedLink: '/assignments/123/', // Selected assignments are not propagated
      },
    ].forEach(({ prop, arg, expectedLink }) => {
      it('preserves filters', () => {
        const wrapper = createComponent();
        updateFilter(wrapper, prop, arg);

        assert.equal(getLinkForId(wrapper, '123'), expectedLink);
      });
    });
  });

  context('when filters are set', () => {
    it('initializes expected filters', () => {
      setCurrentURL('?assignment_id=1&assignment_id=2&student_id=3');

      const wrapper = createComponent();
      const filters = wrapper.find('DashboardActivityFilters');

      // Active course is set from the route
      assert.deepEqual(filters.prop('courses').activeItem, activeCourse);
      // Assignments and students are set from the query
      assert.deepEqual(filters.prop('assignments').selectedIds, ['1', '2']);
      assert.deepEqual(filters.prop('students').selectedIds, ['3']);

      // Selected filters are propagated when loading assignment metrics
      assert.calledWith(fakeUseAPIFetch.lastCall, sinon.match.string, {
        assignment_id: ['1', '2'],
        h_userid: ['3'],
        org_public_id: undefined,
      });
    });

    [
      { query: '', expectedHasSelection: false },
      { query: '?foo=bar', expectedHasSelection: false },
      { query: '?assignment_id=1', expectedHasSelection: true },
      { query: '?student_id=3', expectedHasSelection: true },
      { query: '?assignment_id=1&student_id=3', expectedHasSelection: true },
    ].forEach(({ query, expectedHasSelection }) => {
      it('has `onClearSelection` if one student or one assignment is selected', () => {
        setCurrentURL(query);

        const wrapper = createComponent();
        const filters = wrapper.find('DashboardActivityFilters');

        assert.equal(!!filters.prop('onClearSelection'), expectedHasSelection);
      });
    });

    it('updates query when selected assignments change', () => {
      const wrapper = createComponent();

      updateFilter(wrapper, 'assignments', ['3', '7']);

      assert.equal(location.search, '?assignment_id=3&assignment_id=7');
    });

    it('updates query when selected students change', () => {
      const wrapper = createComponent();

      updateFilter(wrapper, 'students', ['8', '20', '32']);

      assert.equal(
        location.search,
        '?student_id=8&student_id=20&student_id=32',
      );
    });

    it('clears selected students and assignments on clear selection', () => {
      setCurrentURL(
        '?foo=bar&assignment_id=3&assignment_id=7&student_id=8&student_id=20&student_id=32',
      );

      const wrapper = createComponent();
      const filters = wrapper.find('DashboardActivityFilters');

      act(() => filters.props().onClearSelection());

      assert.equal(location.search, '?foo=bar');
    });

    [
      {
        currentSearch: 'current=query',
        expectedDestination: '/?current=query',
      },
      {
        currentSearch: '',
        expectedDestination: '/',
      },
    ].forEach(({ currentSearch, expectedDestination }) => {
      it('navigates to home preserving current query when selected course is cleared', () => {
        fakeUseSearch.returns(currentSearch);

        const wrapper = createComponent();
        const filters = wrapper.find('DashboardActivityFilters');

        act(() => filters.prop('courses').onClear());

        assert.calledWith(fakeNavigate, expectedDestination);
      });
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
