import { formatDateTime } from '@hypothesis/frontend-shared';
import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';
import { act } from 'preact/test-utils';
import sinon from 'sinon';

import { Config } from '../../../config';
import AssignmentActivity, { $imports } from '../AssignmentActivity';

describe('AssignmentActivity', () => {
  const activeStudents = [
    {
      display_name: 'b',
      annotation_metrics: {
        last_activity: '2020-01-01T00:00:00',
        annotations: 8,
        replies: 0,
      },
      auto_grading_grade: {
        current_grade: 0.5,
        last_grade: null,
      },
    },
    {
      display_name: 'a',
      annotation_metrics: {
        last_activity: '2020-01-02T00:00:00',
        annotations: 3,
        replies: 20,
      },
      auto_grading_grade: {
        current_grade: 0.8,
        last_grade: 0.61,
      },
    },
    {
      display_name: 'c',
      annotation_metrics: {
        last_activity: '2020-01-02T00:00:00',
        annotations: 5,
        replies: 100,
      },
      auto_grading_grade: {
        current_grade: 0.4,
        last_grade: null,
      },
    },
  ];
  const activeAssignment = {
    id: 123,
    title: 'The title',
    course: {
      id: 12,
      title: 'The course',
    },
  };

  let fakeUseAPIFetch;
  let fakeUsePolledAPIFetch;
  let fakeNavigate;
  let fakeUseSearch;
  let fakeMutate;
  let fakeConfig;
  let shouldRefreshCallback;
  let wrappers;

  function setUpFakeUseAPIFetch(
    assignment = activeAssignment,
    students = { students: activeStudents },
  ) {
    fakeUseAPIFetch.callsFake(url => ({
      isLoading: false,
      data: url.endsWith('metrics') ? students : assignment,
      mutate: fakeMutate,
    }));
  }

  function setCurrentURL(url) {
    history.replaceState(null, '', url);
  }

  beforeEach(() => {
    setCurrentURL('?');

    fakeUseAPIFetch = sinon.stub();
    setUpFakeUseAPIFetch();

    fakeUsePolledAPIFetch = sinon.stub().callsFake(({ shouldRefresh }) => {
      // Save `shouldRefresh` callback so that we can test its behavior directly
      shouldRefreshCallback = shouldRefresh;

      return {
        data: null,
        isLoading: true,
      };
    });

    fakeNavigate = sinon.stub();
    fakeUseSearch = sinon.stub().returns('current=query');
    fakeMutate = sinon.stub();
    fakeConfig = {
      dashboard: {
        routes: {
          assignment: '/api/assignments/:assignment_id',
          students_metrics: '/api/students/metrics',
          assignment_grades_sync: '/api/assignments/:assignment_id/grades/sync',
        },
        auto_grading_sync_enabled: true,
        assignment_segments_filter_enabled: false,
      },
    };

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
        usePolledAPIFetch: fakeUsePolledAPIFetch,
      },
      'wouter-preact': {
        useParams: sinon.stub().returns({ assignmentId: '123' }),
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
      expectedValue: formatDateTime('2024-01-01T10:35:18'),
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
    [
      {
        extraQuery: '',
        expectedSegments: [],
      },
      {
        extraQuery: '&segment_id=foo',
        expectedSegments: ['foo'],
      },
      {
        extraQuery: '&segment_id=bar&segment_id=baz',
        expectedSegments: ['bar', 'baz'],
      },
    ].forEach(({ expectedSegments, extraQuery }) => {
      it('initializes expected filters', () => {
        setCurrentURL(`?student_id=1&student_id=2${extraQuery}`);

        const wrapper = createComponent();
        const filters = wrapper.find('DashboardActivityFilters');

        // Active course and assignment are set from the route
        assert.deepEqual(
          filters.prop('courses').activeItem,
          activeAssignment.course,
        );
        assert.deepEqual(
          filters.prop('assignments').activeItem,
          activeAssignment,
        );
        // Students are set from the query
        assert.deepEqual(filters.prop('students').selectedIds, ['1', '2']);

        // Selected filters are propagated when loading assignment metrics
        assert.calledWith(fakeUseAPIFetch.lastCall, sinon.match.string, {
          h_userid: ['1', '2'],
          segment_authority_provided_id: expectedSegments,
          assignment_id: '123',
          org_public_id: undefined,
        });
      });
    });

    [
      { query: '', expectedHasSelection: false },
      { query: '?foo=bar', expectedHasSelection: false },
      { query: '?student_id=3', expectedHasSelection: true },
      { query: '?student_id=1&student_id=3', expectedHasSelection: true },
    ].forEach(({ query, expectedHasSelection }) => {
      it('has `onClearSelection` if at least one student is selected', () => {
        setCurrentURL(query);

        const wrapper = createComponent();
        const filters = wrapper.find('DashboardActivityFilters');

        assert.equal(!!filters.prop('onClearSelection'), expectedHasSelection);
      });
    });

    it('updates query when selected students change', () => {
      const wrapper = createComponent();
      const filters = wrapper.find('DashboardActivityFilters');

      act(() => filters.prop('students').onChange(['3', '7']));

      assert.equal(location.search, '?student_id=3&student_id=7');
    });

    it('updates query when selected segments change', () => {
      setUpFakeUseAPIFetch({
        ...activeAssignment,
        groups: [{}, {}],
        auto_grading_config: {},
      });

      const wrapper = createComponent();
      const filters = wrapper.find('DashboardActivityFilters');

      act(() => filters.prop('segments').onChange(['3', '7']));

      assert.equal(location.search, '?segment_id=3&segment_id=7');
    });

    it('clears selected students and segments on clear selection', () => {
      setCurrentURL(
        '?foo=bar&student_id=8&student_id=20&student_id=32&segment_id=foo',
      );

      const wrapper = createComponent();
      const filters = wrapper.find('DashboardActivityFilters');

      act(() => filters.props().onClearSelection());

      assert.equal(location.search, '?foo=bar');
    });

    it('navigates to home page preserving assignment and students when course is cleared', () => {
      setCurrentURL('?student_id=8&student_id=20&student_id=32');

      const wrapper = createComponent();
      const filters = wrapper.find('DashboardActivityFilters');

      act(() => filters.prop('courses').onClear());

      assert.calledWith(
        fakeNavigate,
        '?assignment_id=123&student_id=8&student_id=20&student_id=32',
      );
    });

    [
      {
        currentSearch: 'current=query',
        expectedDestination: '/courses/12?current=query',
      },
      {
        currentSearch: '',
        expectedDestination: '/courses/12',
      },
    ].forEach(({ currentSearch, expectedDestination }) => {
      it('navigates to course preserving current query when selected assignment is cleared', () => {
        fakeUseSearch.returns(currentSearch);

        const wrapper = createComponent();
        const filters = wrapper.find('DashboardActivityFilters');

        act(() => filters.prop('assignments').onClear());

        assert.calledWith(fakeNavigate, expectedDestination);
      });
    });
  });

  context('when auto-grading is enabled', () => {
    [
      {
        autoGradingEnabled: false,
        expectedColumns: [
          {
            field: 'display_name',
            label: 'Student',
          },
          {
            field: 'annotations',
            label: 'Annotations',
            initialOrderDirection: 'descending',
          },
          {
            field: 'replies',
            label: 'Replies',
            initialOrderDirection: 'descending',
          },
          {
            field: 'last_activity',
            label: 'Last Activity',
            initialOrderDirection: 'descending',
          },
        ],
      },
      {
        autoGradingEnabled: true,
        expectedColumns: [
          {
            field: 'display_name',
            label: 'Student',
          },
          {
            field: 'current_grade',
            label: 'Grade',
          },
          {
            field: 'annotations',
            label: 'Annotations',
            initialOrderDirection: 'descending',
          },
          {
            field: 'replies',
            label: 'Replies',
            initialOrderDirection: 'descending',
          },
          {
            field: 'last_activity',
            label: 'Last Activity',
            initialOrderDirection: 'descending',
          },
        ],
      },
    ].forEach(({ autoGradingEnabled, expectedColumns }) => {
      it('shows one more column in the metrics table', () => {
        setUpFakeUseAPIFetch({
          ...activeAssignment,
          auto_grading_config: autoGradingEnabled ? {} : null,
        });

        const wrapper = createComponent();
        const tableElement = wrapper.find('OrderableActivityTable');

        assert.deepEqual(tableElement.prop('columns'), expectedColumns);
      });
    });

    [{ current_grade: undefined }, { current_grade: 25 }].forEach(
      ({ current_grade }) => {
        it('shows the grade for every student', () => {
          setUpFakeUseAPIFetch({
            ...activeAssignment,
            auto_grading_config: {},
          });

          const wrapper = createComponent();
          const item = wrapper
            .find('OrderableActivityTable')
            .props()
            .renderItem({ current_grade }, 'current_grade');
          const gradeIndicator = mount(item).find('GradeIndicator');

          assert.equal(gradeIndicator.prop('grade'), current_grade ?? 0);
        });
      },
    );

    [
      {
        syncEnabled: true,
        isAutoGradingAssignment: true,
        shouldShowButton: true,
      },
      {
        syncEnabled: false,
        isAutoGradingAssignment: true,
        shouldShowButton: false,
      },
      {
        syncEnabled: true,
        isAutoGradingAssignment: false,
        shouldShowButton: false,
      },
      {
        syncEnabled: false,
        isAutoGradingAssignment: false,
        shouldShowButton: false,
      },
    ].forEach(({ isAutoGradingAssignment, syncEnabled, shouldShowButton }) => {
      it('shows sync button when both sync and auto-grading are enabled', () => {
        setUpFakeUseAPIFetch({
          ...activeAssignment,
          auto_grading_config: isAutoGradingAssignment ? {} : null,
        });
        fakeConfig.dashboard.auto_grading_sync_enabled = syncEnabled;

        const wrapper = createComponent();

        assert.equal(wrapper.exists('SyncGradesButton'), shouldShowButton);
      });
    });

    [
      { studentsData: null, expectedStudentsToSync: undefined },
      { studentsData: { students: [] }, expectedStudentsToSync: [] },
      {
        studentsData: {
          students: [
            // Included, because last grade is missing: Student never synced
            {
              display_name: 'a',
              h_userid: 'foo',
              auto_grading_grade: {
                current_grade: 0.5,
              },
            },
            // Included, because last grade and current grade are different
            {
              display_name: 'b',
              h_userid: 'bar',
              auto_grading_grade: {
                current_grade: 0.87,
                last_grade: 0.7,
              },
            },
            // Ignored, because auto_grading_grade is not set
            {
              display_name: 'c',
              h_userid: 'baz',
            },
            // Ignored, because last and current grades are the same
            {
              display_name: 'd',
              h_userid: 'baz',
              auto_grading_grade: {
                current_grade: 0.64,
                last_grade: 0.64,
              },
            },
          ],
        },
        expectedStudentsToSync: [
          { h_userid: 'foo', grade: 0.5 },
          { h_userid: 'bar', grade: 0.87 },
        ],
      },
    ].forEach(({ studentsData, expectedStudentsToSync }) => {
      it('resolves the right list of students to sync', () => {
        setUpFakeUseAPIFetch(
          {
            ...activeAssignment,
            auto_grading_config: {},
          },
          studentsData,
        );
        fakeConfig.dashboard.auto_grading_sync_enabled = true;

        const wrapper = createComponent();

        assert.deepEqual(
          wrapper.find('SyncGradesButton').prop('studentsToSync'),
          expectedStudentsToSync,
        );
      });
    });

    it('updates students once sync has been scheduled', () => {
      setUpFakeUseAPIFetch({
        ...activeAssignment,
        auto_grading_config: {},
      });
      fakeConfig.dashboard.auto_grading_sync_enabled = true;

      const wrapper = createComponent();
      act(() => wrapper.find('SyncGradesButton').props().onSyncScheduled());

      assert.calledWith(fakeMutate, {
        students: activeStudents.map(({ auto_grading_grade, ...rest }) => ({
          ...rest,
          auto_grading_grade: {
            ...auto_grading_grade,
            last_grade: auto_grading_grade.current_grade,
          },
        })),
      });
    });

    [
      {
        fetchResult: { data: null },
        expectedResult: false,
      },
      {
        fetchResult: {
          data: { status: 'scheduled' },
        },
        expectedResult: true,
      },
      {
        fetchResult: {
          data: { status: 'in_progress' },
        },
        expectedResult: true,
      },
      {
        fetchResult: {
          data: { status: 'finished' },
        },
        expectedResult: false,
      },
    ].forEach(({ fetchResult, expectedResult }) => {
      it('shouldRefresh callback behaves as expected', () => {
        createComponent();
        assert.equal(shouldRefreshCallback(fetchResult), expectedResult);
      });
    });

    [
      {
        data: null,
        shouldDisplayLastSyncInfo: false,
        shouldDisplaySyncing: false,
      },
      {
        data: { status: 'scheduled' },
        shouldDisplayLastSyncInfo: true,
        shouldDisplaySyncing: true,
      },
      {
        data: { status: 'in_progress' },
        shouldDisplayLastSyncInfo: true,
        shouldDisplaySyncing: true,
      },
      {
        data: {
          status: 'error',
          finish_date: '2024-10-02T14:24:15.677924+00:00',
        },
        shouldDisplayLastSyncInfo: true,
        shouldDisplaySyncing: false,
      },
      {
        data: {
          status: 'finished',
          finish_date: '2024-10-02T14:24:15.677924+00:00',
        },
        shouldDisplayLastSyncInfo: true,
        shouldDisplaySyncing: false,
      },
    ].forEach(({ data, shouldDisplayLastSyncInfo, shouldDisplaySyncing }) => {
      it('displays the last time grades were synced', () => {
        fakeUsePolledAPIFetch.returns({
          data,
          isLoading: false,
        });

        const wrapper = createComponent();
        const lastSyncDate = wrapper.find('[data-testid="last-sync-date"]');

        assert.equal(lastSyncDate.exists(), shouldDisplayLastSyncInfo);

        if (shouldDisplayLastSyncInfo) {
          assert.equal(
            lastSyncDate.text().includes('syncing…'),
            shouldDisplaySyncing,
          );
        }
      });
    });

    [true, false].forEach(isAutoGradingAssignment => {
      it('should load last time grades were synced only for auto-grading assignments', () => {
        setUpFakeUseAPIFetch({
          ...activeAssignment,
          auto_grading_config: isAutoGradingAssignment ? {} : null,
        });
        createComponent();

        assert.calledWith(
          fakeUsePolledAPIFetch.lastCall,
          sinon.match({
            path: isAutoGradingAssignment ? sinon.match.string : null,
          }),
        );
      });
    });

    [
      { failedGrades: 0, expectedErrorText: null },
      { failedGrades: 1, expectedErrorText: 'Error syncing 1 grade' },
      { failedGrades: 5, expectedErrorText: 'Error syncing 5 grades' },
    ].forEach(({ failedGrades, expectedErrorText }) => {
      it('shows error message when last sync failed', () => {
        setUpFakeUseAPIFetch({
          ...activeAssignment,
          auto_grading_config: {},
        });

        const failed = failedGrades > 0;
        const grades = [{ status: 'finished' }];

        for (let i = 0; i < failedGrades; i++) {
          grades.push({ status: 'failed' });
        }

        fakeUsePolledAPIFetch.returns({
          data: {
            status: failed ? 'failed' : 'finished',
            grades,
          },
          isLoading: false,
        });

        const wrapper = createComponent();
        const errorMessage = wrapper.find('SyncErrorMessage');

        assert.equal(errorMessage.exists(), failed);
        if (failed) {
          assert.equal(errorMessage.text(), expectedErrorText);
        }
      });
    });
  });

  context('when assignment has segments', () => {
    it('sets no segments when auto-grading is not enabled', () => {
      const wrapper = createComponent();
      const filters = wrapper.find('DashboardActivityFilters');

      assert.isUndefined(filters.prop('segments'));
    });

    [
      {
        assignmentExtra: { sections: [{}, {}] },
        expectedType: 'sections',
      },
      {
        assignmentExtra: { sections: [] },
        expectedType: 'sections',
      },
      {
        assignmentExtra: { groups: [{}, {}, {}] },
        expectedType: 'groups',
      },
      {
        assignmentExtra: { groups: [] },
        expectedType: 'groups',
      },
      {
        assignmentExtra: {},
        expectedType: 'none',
      },
    ].forEach(({ assignmentExtra, expectedType }) => {
      it('sets type of segment based on assignment data fields', () => {
        setUpFakeUseAPIFetch({
          ...activeAssignment,
          ...assignmentExtra,
          auto_grading_config: {},
        });

        const wrapper = createComponent();
        const filters = wrapper.find('DashboardActivityFilters');
        const segments = filters.prop('segments');

        assert.equal(segments.type, expectedType);
        assert.deepEqual(segments.entries, assignmentExtra[expectedType] ?? []);
      });
    });

    it('filters have `onClearSelection` if at least one segment is set', () => {
      setCurrentURL('?segment_id=foo');
      setUpFakeUseAPIFetch({
        ...activeAssignment,
        groups: [{}, {}],
        auto_grading_config: {},
      });

      const wrapper = createComponent();
      const filters = wrapper.find('DashboardActivityFilters');

      assert.isDefined(filters.prop('onClearSelection'));
    });
  });

  context('when assignment_segments_filter_enabled is true', () => {
    beforeEach(() => {
      fakeConfig.dashboard.assignment_segments_filter_enabled = true;
    });

    [{ sections: [{}, {}] }, { groups: [{}, {}, {}] }].forEach(
      assignmentExtra => {
        it('shows segments filter dropdown', () => {
          setUpFakeUseAPIFetch({
            ...activeAssignment,
            ...assignmentExtra,
          });

          const wrapper = createComponent();
          const filters = wrapper.find('DashboardActivityFilters');

          assert.isDefined(filters.prop('segments'));
        });
      },
    );
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
