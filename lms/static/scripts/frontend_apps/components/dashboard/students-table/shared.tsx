import type { ComponentChildren } from 'preact';

import type { StudentWithMetrics } from '../../../api-types';
import FormattedDate from '../FormattedDate';
import type { OrderableActivityTableColumn } from '../OrderableActivityTable';
import StudentStatusBadge from '../StudentStatusBadge';
import type { StudentsTableRow } from './types';

export const studentColumn: OrderableActivityTableColumn<StudentsTableRow> = {
  field: 'display_name',
  label: 'Student',
};

/**
 * Last column of every variant.
 *
 * A variant which repeats the other metrics per window still displays this one
 * once, so it is defined apart from them.
 */
export const lastActivityColumn: OrderableActivityTableColumn<StudentsTableRow> =
  {
    field: 'last_activity',
    label: 'Last Activity',
    initialOrderDirection: 'descending',
  };

export const metricsColumns: OrderableActivityTableColumn<StudentsTableRow>[] =
  [
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
    lastActivityColumn,
  ];

/**
 * Flatten every metric of a student into a single row.
 *
 * Every variant displays the same metrics, so they all build their rows this
 * way. `auto_grading_grade` is absent for an assignment without grading, so
 * spreading it is a no-op there.
 *
 * The fields are listed rather than spread from the student so that a row stays
 * a deliberate projection: a table cell holds a single value, and the API also
 * reports data which is not one — `phase_metrics` is a list, and the variant
 * which displays it puts its own fields at the top level.
 */
export function buildRows(students: StudentWithMetrics[]): StudentsTableRow[] {
  return students.map(student => ({
    h_userid: student.h_userid,
    lms_id: student.lms_id,
    display_name: student.display_name,
    active: student.active,
    ...student.auto_grading_grade,
    ...student.annotation_metrics,
  }));
}

/**
 * Render the fields every variant displaying {@link StudentsTableRow} has in
 * common.
 *
 * A field with no renderer of its own is rendered as empty, so that a column
 * this variant does not know about never breaks the table.
 */
export function renderSharedField(
  row: StudentsTableRow,
  field: keyof StudentsTableRow,
): ComponentChildren {
  switch (field) {
    case 'annotations':
    case 'replies':
      return <div className="text-right">{row[field]}</div>;
    case 'last_activity':
      return row.last_activity ? (
        <FormattedDate date={row.last_activity} />
      ) : (
        ''
      );
    case 'display_name':
      return (
        <div className="flex items-center justify-between gap-x-2">
          {row.display_name ?? (
            <span className="flex flex-col gap-1.5">
              <span className="italic">Unknown</span>
              <span className="text-xs text-grey-7">
                This student launched the assignment but didn{"'"}t annotate yet
              </span>
            </span>
          )}
          {!row.active && (
            <div
              className="-my-0.5"
              title="This student is no longer in this assignment"
            >
              <StudentStatusBadge type="drop" />
            </div>
          )}
        </div>
      );
    default:
      return '';
  }
}
