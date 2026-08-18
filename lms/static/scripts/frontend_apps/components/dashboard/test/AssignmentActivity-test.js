import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from '@hypothesis/frontend-testing';
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
      active: true,
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
      active: true,
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
      active: false,
    },
  ];
  const activeAssignment = {
    id: 123,
    title: 'The title',
    course: {
      id: 12,
      title: 'The course',
    },
    is_gradable: true,
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
        user: {
          is_staff: false,
        },
      },
    };

    wrappers = [];

    $imports.$mock(mockImportedComponents());
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

  it('passes the table of the plain variant to the table component', () => {
    const wrapper = createComponent();
    const tableElement = wrapper.find('OrderableActivityTable');

    // An assignment with no grading capability resolves to the plain variant,
    // which displays no grade column
    assert.deepEqual(
      tableElement.prop('columns').map(({ field }) => field),
      ['display_name', 'annotations', 'replies', 'last_activity'],
    );
    assert.lengthOf(tableElement.prop('rows'), activeStudents.length);
  });

  context('when auto-grading is enabled', () => {
    it('passes the table of the auto-grading variant to the table component', () => {
      setUpFakeUseAPIFetch({
        ...activeAssignment,
        auto_grading_config: {},
      });

      const wrapper = createComponent();
      const tableElement = wrapper.find('OrderableActivityTable');

      // What each variant displays is asserted in `students-table`. This only
      // checks that the resolved table reaches the component.
      assert.deepEqual(
        tableElement.prop('columns').map(({ field }) => field),
        [
          'display_name',
          'current_grade',
          'annotations',
          'replies',
          'last_activity',
        ],
      );
      assert.lengthOf(tableElement.prop('rows'), activeStudents.length);

      // The renderer of the variant has to reach the table as well, or every
      // cell of every column renders empty
      const cell = mount(
        tableElement.prop('renderItem')(
          tableElement.prop('rows')[0],
          'annotations',
        ),
      );
      wrappers.push(cell);

      assert.equal(
        cell.text(),
        `${activeStudents[0].annotation_metrics.annotations}`,
      );
    });

    it('indexes the status of the last grades sync by student', () => {
      setUpFakeUseAPIFetch({
        ...activeAssignment,
        auto_grading_config: {},
      });
      fakeUsePolledAPIFetch.returns({
        data: {
          grades: [
            { h_userid: 'abc', status: 'finished' },
            { h_userid: 'def', status: 'failed' },
          ],
        },
        isLoading: false,
      });
      // Spy on the table config, so that the map can be asserted on without
      // rendering the real grade indicator
      const fakeUseStudentsTableConfig = sinon
        .stub()
        .returns({ rows: [], columns: [], renderItem: () => null });
      $imports.$mock({
        './students-table': {
          useStudentsTableConfig: fakeUseStudentsTableConfig,
        },
      });

      createComponent();

      // How the status is displayed is asserted in `students-table`. This
      // checks that the grades of the last sync reach the table indexed by the
      // ID its renderer looks them up by.
      assert.deepEqual(
        fakeUseStudentsTableConfig.lastCall.args[0].studentSyncStatuses,
        { abc: 'finished', def: 'failed' },
      );
    });

    [
      {
        isStaff: true,
        isAutoGradingAssignment: true,
        isGradable: true,
      },
      {
        isStaff: false,
        isAutoGradingAssignment: true,
        isGradable: true,
      },
      {
        isStaff: true,
        isAutoGradingAssignment: false,
        isGradable: true,
      },
      {
        isStaff: false,
        isAutoGradingAssignment: false,
        isGradable: true,
      },
      {
        isStaff: false,
        isAutoGradingAssignment: true,
        isGradable: false,
      },
      {
        isStaff: false,
        isAutoGradingAssignment: false,
        isGradable: true,
      },
      {
        isStaff: true,
        isAutoGradingAssignment: false,
        isGradable: false,
      },
      {
        isStaff: false,
        isAutoGradingAssignment: false,
        isGradable: false,
      },
    ].forEach(({ isAutoGradingAssignment, isStaff, isGradable }) => {
      it('shows sync button when user is not staff, and the assignment is auto-grading and gradable', () => {
        setUpFakeUseAPIFetch({
          ...activeAssignment,
          is_gradable: isGradable,
          auto_grading_config: isAutoGradingAssignment ? {} : null,
        });
        fakeConfig.dashboard.user.is_staff = isStaff;

        const wrapper = createComponent();

        assert.equal(
          wrapper.exists('SyncGradesButton'),
          isAutoGradingAssignment && !isStaff && isGradable,
        );
      });
    });

    it('passes the grades to sync to the sync button', () => {
      setUpFakeUseAPIFetch({
        ...activeAssignment,
        auto_grading_config: {},
      });
      fakeConfig.dashboard.user.is_staff = false;

      const wrapper = createComponent();

      // Which grades need syncing is asserted in `students-table`. This only
      // checks that the resolved list reaches the button: the two active
      // students whose grade changed are included, and the third is left out
      // for being inactive.
      assert.lengthOf(
        wrapper.find('SyncGradesButton').prop('studentsToSync'),
        2,
      );
    });

    it('updates students once sync has been scheduled', () => {
      setUpFakeUseAPIFetch({
        ...activeAssignment,
        auto_grading_config: {},
      });
      fakeConfig.dashboard.user.is_staff = false;

      const wrapper = createComponent();
      act(() => wrapper.find('SyncGradesButton').props().onSyncScheduled());

      assert.calledWith(
        fakeMutate,
        sinon.match({
          students: activeStudents.map(({ auto_grading_grade, ...rest }) => ({
            ...rest,
            auto_grading_grade: {
              ...auto_grading_grade,
              last_grade: auto_grading_grade.current_grade,
            },
          })),
        }),
      );
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
      },
      {
        data: { status: 'scheduled' },
        shouldDisplayLastSyncInfo: true,
      },
      {
        data: { status: 'in_progress' },
        shouldDisplayLastSyncInfo: true,
      },
      {
        data: {
          status: 'error',
          finish_date: '2024-10-02T14:24:15.677924+00:00',
        },
        shouldDisplayLastSyncInfo: true,
      },
      {
        data: {
          status: 'finished',
          finish_date: '2024-10-02T14:24:15.677924+00:00',
        },
        shouldDisplayLastSyncInfo: true,
      },
    ].forEach(({ data, shouldDisplayLastSyncInfo }) => {
      it('displays the last time grades were synced', () => {
        fakeUsePolledAPIFetch.returns({
          data,
          isLoading: false,
        });

        const wrapper = createComponent();
        const lastSyncDate = wrapper.find('[data-testid="last-sync-date"]');

        assert.equal(lastSyncDate.exists(), shouldDisplayLastSyncInfo);
      });
    });

    [
      { lastUpdated: undefined, shouldDisplayLastSyncInfo: false },
      {
        lastUpdated: '2024-10-02T14:24:15.677924+00:00',
        shouldDisplayLastSyncInfo: true,
      },
    ].forEach(({ lastUpdated, shouldDisplayLastSyncInfo }) => {
      it('displays the last time roster was synced', () => {
        setUpFakeUseAPIFetch(activeAssignment, {
          students: activeStudents,
          last_updated: lastUpdated,
        });

        const wrapper = createComponent();
        const lastSyncDate = wrapper.find('[data-testid="last-roster-date"]');
        const missingRosterMessage = wrapper.find(
          '[data-testid="missing-roster-message"]',
        );

        assert.equal(lastSyncDate.exists(), shouldDisplayLastSyncInfo);
        assert.equal(missingRosterMessage.exists(), !shouldDisplayLastSyncInfo);
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
