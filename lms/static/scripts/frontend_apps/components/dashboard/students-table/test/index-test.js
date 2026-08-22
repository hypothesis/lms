import { formatDateTime } from '@hypothesis/frontend-shared';
import { mockImportedComponents, mount } from '@hypothesis/frontend-testing';

import { $imports as autoGradingImports } from '../auto-grading';
import {
  VARIANT_MODULES,
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
  const checkpointAssignment = { ...plainAssignment, checkpoint_enabled: true };
  const gradedCheckpointAssignment = {
    ...checkpointAssignment,
    auto_grading_config: autoGradingAssignment.auto_grading_config,
  };

  let wrappers;

  beforeEach(() => {
    wrappers = [];

    // Only `GradeIndicator` is mocked, so that the props it receives can be
    // asserted on. `FormattedDate` and `StudentStatusBadge` come from the
    // shared field renderer, and are left alone so that their output can be
    // asserted.
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
      { assignment: checkpointAssignment, expectedVariant: 'checkpoint' },
      // Both capabilities at once: the windows own the table, and the grade of
      // each one is displayed inside its group
      {
        assignment: gradedCheckpointAssignment,
        expectedVariant: 'checkpoint-auto-grading',
      },
    ].forEach(({ assignment, expectedVariant }) => {
      it('resolves the variant from the data the assignment exposes', () => {
        assert.equal(resolveVariantModule(assignment).variant, expectedVariant);
      });
    });

    it('falls back to the plain variant, which handles every other assignment', () => {
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
      // A Hide & Reveal assignment which is not graded has nothing to sync
      { assignment: checkpointAssignment, expectedSyncsGrades: false },
      { assignment: gradedCheckpointAssignment, expectedSyncsGrades: true },
    ].forEach(({ assignment, expectedSyncsGrades }) => {
      it('is only true for variants which grade students', () => {
        assert.equal(assignmentSyncsGrades(assignment), expectedSyncsGrades);
      });
    });
  });

  describe('VARIANT_MODULES', () => {
    it('does not let two variants claim the same assignment', () => {
      // A variant owns the assignments whose capabilities are exactly the ones
      // it declares, so the only way two of them can claim the same assignment
      // is by declaring the same set. If that happened the first listed would
      // win silently, including its `gradesToSync`, which is what decides
      // whether the sync button exists at all.
      const declared = VARIANT_MODULES.map(({ handles }) =>
        [...handles].sort().join('+'),
      );

      assert.deepEqual(declared, [...new Set(declared)]);
    });

    it('declares every capability of a variant which handles more than one', () => {
      // The variants which handle a combination have to declare each of its
      // parts: a missing one would leave the combination to a more basic
      // variant, and this is what replaces the mutually exclusive predicates
      // the registry used to need.
      assert.deepEqual(
        VARIANT_MODULES.map(({ variant, handles }) => [
          variant,
          [...handles].sort(),
        ]),
        [
          ['auto-grading', ['auto-grading']],
          ['checkpoint', ['checkpoints']],
          ['checkpoint-auto-grading', ['auto-grading', 'checkpoints']],
        ],
      );
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

  describe('checkpoint variants', () => {
    // Shape the API reports: one entry per grading phase, 1-based, with the
    // boundary `h` worked out from the reveals and the due date
    const phaseMetrics = [
      {
        phase: 1,
        ends_at: '2024-01-02T00:00:00',
        metrics: { annotations: 5, replies: 1, last_activity: null },
        grade: 0.5,
      },
      {
        phase: 2,
        ends_at: '2024-01-05T00:00:00',
        metrics: { annotations: 3, replies: 2, last_activity: null },
        grade: 0.75,
      },
    ];
    const student = {
      h_userid: 'acct:a@lms.hypothes.is',
      lms_id: '1',
      display_name: 'a',
      active: true,
      annotation_metrics: {
        annotations: 8,
        replies: 3,
        last_activity: '2024-01-01T10:35:18',
      },
      auto_grading_grade: { current_grade: 0.6, last_grade: null },
    };

    function config(
      assignment,
      students = [{ ...student, phase_metrics: phaseMetrics }],
    ) {
      return renderHook(useStudentsTableConfig, {
        students,
        assignment,
        studentSyncStatuses: {},
      }).result;
    }

    it('displays the metrics of every phase under its own header', () => {
      const { columns } = config(checkpointAssignment);

      assert.deepEqual(
        columns.map(({ field, group }) => [field, group]),
        [
          ['display_name', undefined],
          ['phase_1_annotations', 'Checkpoint'],
          ['phase_1_replies', 'Checkpoint'],
          ['phase_2_annotations', 'Due Date'],
          ['phase_2_replies', 'Due Date'],
          ['last_activity', undefined],
        ],
      );
    });

    it('adds a grade per phase and a final grade when the assignment is auto-graded', () => {
      const { columns } = config(gradedCheckpointAssignment);

      assert.deepEqual(
        columns.map(({ field, group }) => [field, group]),
        [
          ['display_name', undefined],
          ['phase_1_grade', 'Checkpoint'],
          ['phase_1_annotations', 'Checkpoint'],
          ['phase_1_replies', 'Checkpoint'],
          ['phase_2_grade', 'Due Date'],
          ['phase_2_annotations', 'Due Date'],
          ['phase_2_replies', 'Due Date'],
          // The grade the LMS gets is the final one, outside every phase
          ['current_grade', 'Final grade'],
          ['last_activity', undefined],
        ],
      );
    });

    it('numbers the checkpoints when there is more than one', () => {
      // The API reports the position of a phase, not a name: the last phase
      // closes at the due date and the others are checkpoints
      const { columns } = config(checkpointAssignment, [
        {
          ...student,
          phase_metrics: [
            ...phaseMetrics,
            {
              phase: 3,
              ends_at: null,
              metrics: { annotations: 0, replies: 0, last_activity: null },
            },
          ],
        },
      ]);

      assert.deepEqual(
        [...new Set(columns.map(({ group }) => group).filter(Boolean))],
        ['Checkpoint 1', 'Checkpoint 2', 'Due Date'],
      );
    });

    it('does not call the first phase the due date before anyone reaches the next', () => {
      // The day after a reveal nobody has activity in the phase which closes at
      // the due date, so the API only reports phase 1. An assignment with a
      // checkpoint always has a phase after it
      const { columns } = config(checkpointAssignment, [
        {
          ...student,
          phase_metrics: [phaseMetrics[0]],
        },
      ]);

      assert.deepEqual(
        columns.map(({ field, group }) => [field, group]),
        [
          ['display_name', undefined],
          ['phase_1_annotations', 'Checkpoint'],
          ['phase_1_replies', 'Checkpoint'],
          ['last_activity', undefined],
        ],
      );
    });

    it('formats the grade of a phase like the final grade of the row', () => {
      // A grade which is not a round percentage must not read as one: rounding
      // 0.999 to "100%" would show a student who missed the requirement as
      // having met it
      const { rows, renderItem } = config(gradedCheckpointAssignment, [
        {
          ...student,
          phase_metrics: [{ ...phaseMetrics[0], grade: 1 / 3 }],
        },
      ]);

      assert.equal(
        mountItem(renderItem(rows[0], 'phase_1_grade')).text(),
        '33.33%',
      );
    });

    it('labels the phases by position when the API skips one', () => {
      // The API only reports the phases a student was active in, so the
      // positions can have holes: labelling by how many came back would call
      // phase 2 the due date and leave two groups sharing a label
      const { columns } = config(checkpointAssignment, [
        {
          ...student,
          phase_metrics: [
            phaseMetrics[1],
            {
              phase: 3,
              ends_at: null,
              metrics: { annotations: 1, replies: 0, last_activity: null },
            },
          ],
        },
      ]);

      assert.deepEqual(
        columns.map(({ field, group }) => [field, group]),
        [
          ['display_name', undefined],
          ['phase_2_annotations', 'Checkpoint 2'],
          ['phase_2_replies', 'Checkpoint 2'],
          ['phase_3_annotations', 'Due Date'],
          ['phase_3_replies', 'Due Date'],
          ['last_activity', undefined],
        ],
      );
    });

    it('flattens the metrics of each phase into the row', () => {
      const { rows } = config(gradedCheckpointAssignment);

      assert.deepInclude(rows[0], {
        // The totals stay in the row, which is what the fallback columns and
        // every other variant display
        annotations: 8,
        replies: 3,
        phase_1_annotations: 5,
        phase_1_replies: 1,
        phase_1_grade: 0.5,
        phase_2_annotations: 3,
        phase_2_replies: 2,
        phase_2_grade: 0.75,
        current_grade: 0.6,
      });
    });

    it('does not leak the phases into the row', () => {
      // A row holds one value per cell; an array in it would break ordering
      const { rows } = config(gradedCheckpointAssignment);

      assert.notProperty(rows[0], 'phase_metrics');
    });

    [
      { field: 'phase_1_annotations', expectedValue: '5' },
      { field: 'phase_2_replies', expectedValue: '2' },
      // A grade is displayed as a percentage, the way the grade column of the
      // auto-grading variant is
      { field: 'phase_1_grade', expectedValue: '50%' },
      { field: 'phase_2_grade', expectedValue: '75%' },
      // A field every variant has in common falls back to the shared renderer
      { field: 'display_name', expectedValue: 'a' },
      {
        field: 'last_activity',
        expectedValue: formatDateTime('2024-01-01T10:35:18'),
      },
    ].forEach(({ field, expectedValue }) => {
      it('renders the cell of a phase', () => {
        const { rows, renderItem } = config(gradedCheckpointAssignment);

        assert.equal(
          mountItem(renderItem(rows[0], field)).text(),
          expectedValue,
        );
      });
    });

    it('leaves the cell of a phase empty when the metric is missing', () => {
      // The API only reports the grade of a phase for an auto-graded
      // assignment, so the field exists in the row without a value
      const { rows, renderItem } = config(checkpointAssignment, [
        {
          ...student,
          phase_metrics: [
            {
              phase: 1,
              ends_at: null,
              metrics: { annotations: 5, replies: 1, last_activity: null },
            },
          ],
        },
      ]);

      assert.equal(renderItem(rows[0], 'phase_1_grade'), '');
    });

    it('renders the final grade through the grade indicator', () => {
      const { rows, renderItem } = config(gradedCheckpointAssignment);

      const gradeIndicator = mountItem(
        renderItem(rows[0], 'current_grade'),
      ).find('GradeIndicator');

      assert.deepInclude(gradeIndicator.props(), {
        grade: 0.6,
        config: gradedCheckpointAssignment.auto_grading_config,
      });
    });

    describe('when the activity is not split into phases yet', () => {
      // The backend does not bucket the annotation counts by phase yet, so a
      // Hide & Reveal assignment has to keep displaying the totals instead of a
      // grid of empty cells
      [
        {
          label: 'without grading',
          assignment: checkpointAssignment,
          expectedFields: [
            'display_name',
            'annotations',
            'replies',
            'last_activity',
          ],
        },
        {
          label: 'with grading',
          assignment: gradedCheckpointAssignment,
          expectedFields: [
            'display_name',
            'current_grade',
            'annotations',
            'replies',
            'last_activity',
          ],
        },
      ].forEach(({ label, assignment, expectedFields }) => {
        it(`displays the same columns as an assignment ${label} and no phases`, () => {
          const { columns } = config(assignment, [student]);

          assert.deepEqual(fieldsOf(columns), expectedFields);
          assert.deepEqual(
            columns.map(({ group }) => group),
            expectedFields.map(() => undefined),
            'no column declares a group, so the flat table is used',
          );
        });
      });

      it('displays only the phases which are reported', () => {
        const { columns } = config(checkpointAssignment, [
          { ...student, phase_metrics: [phaseMetrics[1]] },
        ]);

        assert.deepEqual(fieldsOf(columns), [
          'display_name',
          'phase_2_annotations',
          'phase_2_replies',
          'last_activity',
        ]);
      });

      it('picks up the phases once the metrics arrive', () => {
        // `columns` is memoized, so a request which resolves with the bucketed
        // metrics only reaches the table if the students are a dependency
        const table = renderHook(useStudentsTableConfig, {
          students: [student],
          assignment: checkpointAssignment,
          studentSyncStatuses: {},
        });

        assert.notInclude(
          fieldsOf(table.result.columns),
          'phase_1_annotations',
        );

        table.rerender({
          students: [{ ...student, phase_metrics: phaseMetrics }],
        });

        assert.include(fieldsOf(table.result.columns), 'phase_1_annotations');
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
