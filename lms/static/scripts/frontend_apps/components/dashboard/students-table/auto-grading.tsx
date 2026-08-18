import classnames from 'classnames';
import type { ComponentChildren } from 'preact';

import type { StudentWithMetrics } from '../../../api-types';
import GradeIndicator from '../GradeIndicator';
import type { OrderableActivityTableColumn } from '../OrderableActivityTable';
import {
  buildRows,
  metricsColumns,
  renderPlainField,
  studentColumn,
} from './plain';
import type {
  ConditionalVariantModule,
  GradeToSync,
  RenderContext,
  StudentsTableRow,
} from './types';

const gradeColumn: OrderableActivityTableColumn<StudentsTableRow> = {
  field: 'current_grade',
  label: 'Grade',
};

/** Render the grade of a student, and fall back to the plain fields. */
function renderAutoGradingField(
  row: StudentsTableRow,
  field: keyof StudentsTableRow,
  { assignment, studentSyncStatuses }: RenderContext,
): ComponentChildren {
  if (field !== 'current_grade') {
    return renderPlainField(row, field);
  }

  return (
    <div
      className={classnames(
        // Add a bit of vertical negative margin to avoid the chip
        // component to make rows too tall
        '-my-0.5',
      )}
    >
      <GradeIndicator
        grade={row.current_grade ?? 0}
        lastGrade={row.last_grade}
        annotations={row.annotations}
        replies={row.replies}
        status={studentSyncStatuses[row.h_userid]}
        config={assignment?.auto_grading_config}
      />
    </div>
  );
}

/**
 * Grades of the active students whose current grade differs from the last one
 * synced. A student whose grade has not changed is not synced again.
 */
function gradesToSync(students: StudentWithMetrics[]): GradeToSync[] {
  return students
    .filter(
      ({ auto_grading_grade, active }) =>
        active &&
        !!auto_grading_grade &&
        auto_grading_grade.current_grade !== auto_grading_grade.last_grade,
    )
    .map(({ h_userid, auto_grading_grade }) => ({
      h_userid,
      grade: auto_grading_grade?.current_grade ?? 0,
    }));
}

/**
 * Annotation metrics plus the grade calculated from them, which can be synced
 * to the LMS.
 */
export const autoGradingVariant: ConditionalVariantModule = {
  variant: 'auto-grading',
  matches: assignment => !!assignment?.auto_grading_config,
  buildRows,
  columns: () => [studentColumn, gradeColumn, ...metricsColumns],
  renderItem: renderAutoGradingField,
  gradesToSync,
};
