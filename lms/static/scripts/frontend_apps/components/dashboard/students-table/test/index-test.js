import { formatDateTime } from '@hypothesis/frontend-shared';
import { mockImportedComponents, mount } from '@hypothesis/frontend-testing';

import { $imports as autoGradingImports } from '../auto-grading';
import {
  assignmentSyncsGrades,
  resolveVariantModule,
  useStudentsTableConfig,
  useStudentsToSync,
} from '../index';

describe('students-table', () => {
  const autoGradingAssignment = {
    id: 123,
    title: 'The title',
    is_gradable: true,
    auto_grading_config: {
      grading_type: 'all_or_nothing',
      activity_calculation: 'cumulative',
      required_annotations: 1,
      required_replies: 0,
    },
  };
  const plainAssignment = { id: 123, title: 'The title', is_gradable: true };

  let wrappers;

  beforeEach(() => {
    wrappers = [];

    // Only `GradeIndicator` is mocked, so that the props it receives can be
    // asserted on. `FormattedDate` and `StudentStatusBadge` are rendered by the
    // plain variant, and are left alone so that their output can be asserted.
    autoGradingImports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    wrappers.forEach(wrapper => wrapper.unmount());
    autoGradingImports.$restore();
  });

  /**
   * Mount a component which calls `hook` with `props`, and return its last
   * result plus a way to render it again with different props.
   *
   * These hooks memoize on their arguments, so an incomplete dependency list
   * only shows up across renders: the first one always returns fresh values.
   */
  function renderHook(hook, props) {
    let result;

    function Probe(props) {
      result = hook(props);
      return null;
    }

    const wrapper = mount(<Probe {...props} />);
    wrappers.push(wrapper);

    return {
      get result() {
        return result;
      },

      /** Render again, merging `nextProps` into the current ones. */
      rerender(nextProps) {
        wrapper.setProps(nextProps);
      },
    };
  }

  /** Fields of a list of columns, in display order. */
  function fieldsOf(columns) {
    return columns.map(({ field }) => field);
  }

  /** Mount a cell rendered by a variant, so that `afterEach` unmounts it. */
  function mountItem(item) {
    const wrapper = mount(item);
    wrappers.push(wrapper);

    return wrapper;
  }

  describe('resolveVariantModule', () => {
    [
      { assignment: undefined, expectedVariant: 'plain' },
      { assignment: null, expectedVariant: 'plain' },
      { assignment: plainAssignment, expectedVariant: 'plain' },
      { assignment: autoGradingAssignment, expectedVariant: 'auto-grading' },
    ].forEach(({ assignment, expectedVariant }) => {
      it('resolves the variant from the data the assignment exposes', () => {
        assert.equal(resolveVariantModule(assignment).variant, expectedVariant);
      });
    });

    it('falls back to the plain variant, which matches every assignment', () => {
      // An assignment with a capability this version of the frontend does not
      // know about must still render, rather than matching no variant at all.
      //
      // Note this is NOT `sections`: that field already exists and holds the
      // course sections of the LMS, which every variant ignores.
      const futureAssignment = {
        ...plainAssignment,
        some_future_capability: {},
      };

      assert.equal(resolveVariantModule(futureAssignment).variant, 'plain');
    });

    it('ignores the course sections of the assignment', () => {
      // `sections` feeds the segments filter, not the table variant. A future
      // variant keyed on time windows must not reuse this field name.
      const withCourseSections = {
        ...plainAssignment,
        sections: [{ h_authority_provided_id: 'abc', name: 'Another section' }],
      };

      assert.equal(resolveVariantModule(withCourseSections).variant, 'plain');
    });
  });

  describe('assignmentSyncsGrades', () => {
    [
      { assignment: undefined, expectedSyncsGrades: false },
      { assignment: plainAssignment, expectedSyncsGrades: false },
      { assignment: autoGradingAssignment, expectedSyncsGrades: true },
    ].forEach(({ assignment, expectedSyncsGrades }) => {
      it('is only true for variants which grade students', () => {
        assert.equal(assignmentSyncsGrades(assignment), expectedSyncsGrades);
      });
    });
  });

  describe('useStudentsTableConfig', () => {
    const students = [
      {
        h_userid: 'acct:a@lms.hypothes.is',
        lms_id: '1',
        display_name: 'a',
        active: true,
        annotation_metrics: {
          annotations: 8,
          replies: 3,
          last_activity: '2024-01-01T10:35:18',
        },
        auto_grading_grade: {
          current_grade: 0.5,
          last_grade: null,
          last_grade_date: null,
        },
      },
    ];

    function renderConfig(options = {}) {
      return renderHook(useStudentsTableConfig, {
        students,
        assignment: autoGradingAssignment,
        studentSyncStatuses: {},
        ...options,
      });
    }

    function config(options) {
      return renderConfig(options).result;
    }

    it('flattens metrics and grades into a single row', () => {
      const { rows } = config();

      assert.deepEqual(rows, [
        {
          h_userid: 'acct:a@lms.hypothes.is',
          lms_id: '1',
          display_name: 'a',
          active: true,
          annotations: 8,
          replies: 3,
          last_activity: '2024-01-01T10:35:18',
          current_grade: 0.5,
          last_grade: null,
          last_grade_date: null,
        },
      ]);
    });

    it('returns no rows while students are being loaded', () => {
      const { rows } = config({ students: undefined });

      assert.deepEqual(rows, []);
    });

    it('rebuilds the rows when the students change', () => {
      const table = renderConfig();

      assert.lengthOf(table.result.rows, 1);

      table.rerender({ students: [] });

      assert.deepEqual(table.result.rows, []);
    });

    it('switches variant when the assignment finishes loading', () => {
      // The assignment is not known on the first render, so the table starts
      // on the plain variant and has to pick up the grade column once the
      // request resolves
      const table = renderConfig({ assignment: undefined });

      assert.notInclude(fieldsOf(table.result.columns), 'current_grade');

      table.rerender({ assignment: autoGradingAssignment });

      assert.include(fieldsOf(table.result.columns), 'current_grade');
    });

    it('renders the status a student has after the most recent sync', () => {
      const table = renderConfig({
        studentSyncStatuses: { 'acct:a@lms.hypothes.is': 'in_progress' },
      });
      const renderedStatus = () =>
        mountItem(
          table.result.renderItem(table.result.rows[0], 'current_grade'),
        )
          .find('GradeIndicator')
          .prop('status');

      assert.equal(renderedStatus(), 'in_progress');

      // `renderItem` is memoized, so a sync which just finished only reaches
      // the cell if the statuses are one of its dependencies
      table.rerender({
        studentSyncStatuses: { 'acct:a@lms.hypothes.is': 'finished' },
      });

      assert.equal(renderedStatus(), 'finished');
    });

    it('renders the auto-grading config the assignment currently has', () => {
      const table = renderConfig();
      const renderedConfig = () =>
        mountItem(
          table.result.renderItem(table.result.rows[0], 'current_grade'),
        )
          .find('GradeIndicator')
          .prop('config');

      assert.equal(renderedConfig(), autoGradingAssignment.auto_grading_config);

      // Re-fetching the assignment can change its grading config without
      // changing which variant handles it, so the assignment has to be a
      // dependency of the memoized renderer too
      const regraded = {
        ...autoGradingAssignment,
        auto_grading_config: {
          ...autoGradingAssignment.auto_grading_config,
          required_annotations: 5,
        },
      };
      table.rerender({ assignment: regraded });

      assert.equal(renderedConfig(), regraded.auto_grading_config);
    });

    const studentColumn = { field: 'display_name', label: 'Student' };
    const gradeColumn = { field: 'current_grade', label: 'Grade' };
    const metricsColumns = [
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
    ];

    [
      {
        assignment: plainAssignment,
        expectedColumns: [studentColumn, ...metricsColumns],
      },
      {
        assignment: autoGradingAssignment,
        // The grade is displayed right after the student it belongs to
        expectedColumns: [studentColumn, gradeColumn, ...metricsColumns],
      },
    ].forEach(({ assignment, expectedColumns }) => {
      it('displays the columns of the variant, in order', () => {
        const { columns } = config({ assignment });

        assert.deepEqual(columns, expectedColumns);
      });
    });

    it('passes the auto-grading config and sync status to the grade indicator', () => {
      const { rows, renderItem } = config({
        studentSyncStatuses: { 'acct:a@lms.hypothes.is': 'finished' },
      });

      const gradeIndicator = mountItem(
        renderItem(rows[0], 'current_grade'),
      ).find('GradeIndicator');

      assert.deepInclude(gradeIndicator.props(), {
        grade: 0.5,
        lastGrade: null,
        annotations: 8,
        replies: 3,
        status: 'finished',
        config: autoGradingAssignment.auto_grading_config,
      });
    });

    [
      { currentGrade: 0.5, expectedGrade: 0.5 },
      // A student the API has not graded yet is displayed as a zero rather
      // than as an empty cell
      { currentGrade: undefined, expectedGrade: 0 },
    ].forEach(({ currentGrade, expectedGrade }) => {
      it('shows the grade of every student', () => {
        const { rows, renderItem } = config();
        const row = { ...rows[0], current_grade: currentGrade };

        const gradeIndicator = mountItem(renderItem(row, 'current_grade')).find(
          'GradeIndicator',
        );

        assert.equal(gradeIndicator.prop('grade'), expectedGrade);
      });
    });

    [
      { studentSyncStatuses: {}, expectedStatus: undefined },
      // A sync which did not include this student leaves it without status
      { studentSyncStatuses: { other: 'failed' }, expectedStatus: undefined },
      {
        studentSyncStatuses: { 'acct:a@lms.hypothes.is': 'in_progress' },
        expectedStatus: 'in_progress',
      },
    ].forEach(({ studentSyncStatuses, expectedStatus }) => {
      it('passes the sync status of the student to the grade indicator', () => {
        const { rows, renderItem } = config({ studentSyncStatuses });

        const gradeIndicator = mountItem(
          renderItem(rows[0], 'current_grade'),
        ).find('GradeIndicator');

        assert.equal(gradeIndicator.prop('status'), expectedStatus);
      });
    });

    it('does not display a grade in the plain variant', () => {
      const { rows, renderItem } = config({ assignment: plainAssignment });

      assert.equal(renderItem(rows[0], 'current_grade'), '');
    });

    [
      { field: 'display_name', expectedValue: 'a' },
      { field: 'annotations', expectedValue: '8' },
      { field: 'replies', expectedValue: '3' },
      {
        field: 'last_activity',
        expectedValue: formatDateTime('2024-01-01T10:35:18'),
      },
      // A field with no renderer of its own
      { field: 'lms_id', expectedValue: '' },
    ].forEach(({ field, expectedValue }) => {
      it('renders each field of a row', () => {
        const { rows, renderItem } = config();

        const item = renderItem(rows[0], field);
        const value = typeof item === 'string' ? item : mountItem(item).text();

        assert.equal(value, expectedValue);
      });
    });

    [
      {
        row: { display_name: null, active: true },
        expectedValue:
          "UnknownThis student launched the assignment but didn't annotate yet",
      },
      { row: { display_name: 'a', active: false }, expectedValue: 'aDrop' },
      // Both fallbacks at once: a student who never annotated and is no longer
      // in the assignment
      {
        row: { display_name: null, active: false },
        expectedValue:
          "UnknownThis student launched the assignment but didn't annotate yetDrop",
      },
      {
        row: { display_name: 'a', last_activity: null },
        field: 'last_activity',
      },
    ].forEach(({ row, field = 'display_name', expectedValue = '' }) => {
      it('renders the fallbacks of a row with missing data', () => {
        const { renderItem } = config();

        const item = renderItem(row, field);
        const value = typeof item === 'string' ? item : mountItem(item).text();

        assert.equal(value, expectedValue);
      });
    });
  });

  describe('useStudentsToSync', () => {
    const gradedStudents = [
      // Included, because last grade is missing: student was never synced
      {
        h_userid: 'foo',
        active: true,
        auto_grading_grade: { current_grade: 0.5 },
      },
      // Included, because last and current grades are different
      {
        h_userid: 'bar',
        active: true,
        auto_grading_grade: { current_grade: 0.87, last_grade: 0.7 },
      },
      // Ignored, because there is no grade
      { h_userid: 'baz', active: true },
      // Ignored, because last and current grades are the same
      {
        h_userid: 'qux',
        active: true,
        auto_grading_grade: { current_grade: 0.64, last_grade: 0.64 },
      },
      // Ignored, because the student is no longer active
      {
        h_userid: 'quux',
        active: false,
        auto_grading_grade: { current_grade: 0.5 },
      },
    ];

    [
      // Students are not known yet
      {
        assignment: autoGradingAssignment,
        students: undefined,
        expectedGrades: undefined,
      },
      // A variant which does not grade never syncs, even once students are
      // known
      {
        assignment: plainAssignment,
        students: gradedStudents,
        expectedGrades: undefined,
      },
      {
        assignment: autoGradingAssignment,
        students: [],
        expectedGrades: [],
      },
      {
        assignment: autoGradingAssignment,
        students: gradedStudents,
        expectedGrades: [
          { h_userid: 'foo', grade: 0.5 },
          { h_userid: 'bar', grade: 0.87 },
        ],
      },
    ].forEach(({ assignment, students, expectedGrades }) => {
      it('resolves the grades to sync for the variant', () => {
        const { result } = renderHook(useStudentsToSync, {
          students,
          assignment,
        });

        assert.deepEqual(result, expectedGrades);
      });
    });

    it('recomputes the grades when the students change', () => {
      const sync = renderHook(useStudentsToSync, {
        students: gradedStudents,
        assignment: autoGradingAssignment,
      });

      assert.lengthOf(sync.result, 2);

      // A student whose grade was just synced drops off the list, so a stale
      // memo would keep offering to sync grades the LMS already has
      sync.rerender({
        students: gradedStudents.map(student => ({
          ...student,
          auto_grading_grade: student.auto_grading_grade && {
            ...student.auto_grading_grade,
            last_grade: student.auto_grading_grade.current_grade,
          },
        })),
      });

      assert.deepEqual(sync.result, []);
    });
  });
});
