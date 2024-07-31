import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import { act } from 'preact/test-utils';
import sinon from 'sinon';

import { Config } from '../../../config';
import { formatDateTime } from '../../../utils/date';
import AssignmentActivity, { $imports } from '../AssignmentActivity';

describe('AssignmentActivity', () => {
  const students = [
    {
      display_name: 'b',
      annotation_metrics: {
        last_activity: '2020-01-01T00:00:00',
        annotations: 8,
        replies: 0,
      },
    },
    {
      display_name: 'a',
      annotation_metrics: {
        last_activity: '2020-01-02T00:00:00',
        annotations: 3,
        replies: 20,
      },
    },
    {
      display_name: 'c',
      annotation_metrics: {
        last_activity: '2020-01-02T00:00:00',
        annotations: 5,
        replies: 100,
      },
    },
  ];

  let fakeUseAPIFetch;
  let fakeConfig;
  let fakeNavigate;
  let wrappers;

  beforeEach(() => {
    fakeUseAPIFetch = sinon.stub().callsFake(url => ({
      isLoading: false,
      data: url.endsWith('metrics')
        ? { students }
        : {
            title: 'The title',
            course: {
              id: '357',
              title: 'The course',
            },
          },
    }));
    fakeConfig = {
      dashboard: {
        routes: {
          assignment: '/api/assignments/:assignment_id',
          students_metrics: '/api/students/metrics',
        },
      },
    };
    fakeNavigate = sinon.stub();
    wrappers = [];

    $imports.$mock(mockImportedComponents());
    $imports.$restore({
      // Do not mock FormattedDate, for consistency when checking
      // rendered values in different columns
      './FormattedDate': true,
    });
    $imports.$mock({
      '../../utils/api': {
        useAPIFetch: fakeUseAPIFetch,
      },
      'wouter-preact': {
        useParams: sinon.stub().returns({ assignmentId: '777' }),
        useSearch: sinon.stub().returns('current=query'),
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
        <AssignmentActivity />
      </Config.Provider>,
    );
    wrappers.push(wrapper);

    return wrapper;
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

    assert.equal(titleElement.text(), 'Could not load assignment title');
    assert.equal(tableElement.prop('emptyMessage'), 'Could not load students');
  });

  it('shows expected title', () => {
    const wrapper = createComponent();
    const titleElement = wrapper.find('[data-testid="title"]');
    const tableElement = wrapper.find('OrderableActivityTable');
    const expectedTitle = 'The title';

    assert.equal(titleElement.text(), expectedTitle);
    assert.equal(tableElement.prop('title'), expectedTitle);
  });

  it('shows empty students message', () => {
    const wrapper = createComponent();
    const tableElement = wrapper.find('OrderableActivityTable');

    assert.equal(tableElement.prop('emptyMessage'), 'No students found');
  });

  [
    { fieldName: 'display_name', expectedValue: 'Jane Doe' },
    { fieldName: 'annotations', expectedValue: '37' },
    { fieldName: 'replies', expectedValue: '25' },
    {
      fieldName: 'last_activity',
      expectedValue: formatDateTime(new Date('2024-01-01T10:35:18')),
    },
    // Render "unknown" field name
    { fieldName: 'id', expectedValue: '' },
    // Render last_activity when it's null
    {
      fieldName: 'last_activity',
      expectedValue: '',
      studentStats: { last_activity: null },
    },
    // Render display_name when it's null
    {
      fieldName: 'display_name',
      expectedValue:
        "UnknownThis student launched the assignment but didn't annotate yet",
      studentStats: {
        id: 'e4ca30ee27eda1169d00b83f2a86e3494ffd9b12',
        display_name: null,
      },
    },
  ].forEach(({ fieldName, expectedValue, studentStats }) => {
    it('renders every field as expected', () => {
      const fallbackStudentStats = {
        display_name: 'Jane Doe',
        last_activity: '2024-01-01T10:35:18',
        annotations: 37,
        replies: 25,
      };
      const wrapper = createComponent();

      const item = wrapper
        .find('OrderableActivityTable')
        .props()
        .renderItem(studentStats ?? fallbackStudentStats, fieldName);
      const value = typeof item === 'string' ? item : mount(item).text();

      assert.equal(value, expectedValue);
    });
  });

  context('when filters are set', () => {
    function setCurrentURL(url) {
      history.replaceState(null, '', url);
    }

    beforeEach(() => {
      setCurrentURL('?');
    });

    it('initializes expected filters', () => {
      setCurrentURL('?student_id=123&student_id=456');

      const wrapper = createComponent();
      const filters = wrapper.find('DashboardActivityFilters');

      // Course ID is set from the assignment data
      assert.deepEqual(filters.prop('selectedCourseIds'), ['357']);
      // Assignment ID is set from the route
      assert.deepEqual(filters.prop('selectedAssignmentIds'), ['777']);
      // Students are set from the query
      assert.deepEqual(filters.prop('selectedStudentIds'), ['123', '456']);

      // Selected filters are propagated when loading assignment metrics
      assert.calledWith(fakeUseAPIFetch.lastCall, sinon.match.string, {
        assignment_id: '777',
        h_userid: ['123', '456'],
        public_id: undefined,
      });
    });

    [
      { query: '', expectedHasSelection: false },
      { query: '?foo=bar', expectedHasSelection: false },
      { query: '?student_id=3', expectedHasSelection: true },
      { query: '?student_id=3&student_id=4', expectedHasSelection: true },
    ].forEach(({ query, expectedHasSelection }) => {
      it('has `onClearSelection` if one student is selected', () => {
        setCurrentURL(query);

        const wrapper = createComponent();
        const filters = wrapper.find('DashboardActivityFilters');

        assert.equal(!!filters.prop('onClearSelection'), expectedHasSelection);
      });
    });

    it('updates query when selected students change', () => {
      const wrapper = createComponent();
      const filters = wrapper.find('DashboardActivityFilters');

      act(() => filters.props().onStudentsChange(['8', '20', '32']));

      assert.equal(
        location.search,
        '?student_id=8&student_id=20&student_id=32',
      );
    });

    it('clears selected students on clear selection', () => {
      setCurrentURL('?bar=foo&student_id=8&student_id=20&student_id=32');

      const wrapper = createComponent();
      const filters = wrapper.find('DashboardActivityFilters');

      act(() => filters.props().onClearSelection());

      assert.equal(location.search, '?bar=foo');
    });

    it('navigates to home preserving current query when no course is selected', () => {
      const wrapper = createComponent();
      const filters = wrapper.find('DashboardActivityFilters');

      act(() => filters.props().onCoursesChange([]));

      assert.calledWith(fakeNavigate, '?current=query&assignment_id=777');
    });

    it('navigates to the first selected course which is not active one', () => {
      const wrapper = createComponent();
      const filters = wrapper.find('DashboardActivityFilters');

      act(() => filters.props().onCoursesChange(['357', '123', '789']));

      assert.calledWith(
        fakeNavigate,
        '/courses/123?current=query&assignment_id=777',
      );
    });

    it("navigates to active assignment's course preserving current query when no assignment is selected", () => {
      const wrapper = createComponent();
      const filters = wrapper.find('DashboardActivityFilters');

      act(() => filters.props().onAssignmentsChange([]));

      assert.calledWith(fakeNavigate, '/courses/357?current=query');
    });

    it('navigates to the first selected assignment which is not active one', () => {
      const wrapper = createComponent();
      const filters = wrapper.find('DashboardActivityFilters');

      act(() => filters.props().onAssignmentsChange(['777', '888']));

      assert.calledWith(fakeNavigate, '/assignments/888?current=query');
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
