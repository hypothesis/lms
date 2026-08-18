import type { ComponentChildren } from 'preact';

import type { StudentWithMetrics } from '../../../api-types';
import FormattedDate from '../FormattedDate';
import type { OrderableActivityTableColumn } from '../OrderableActivityTable';
import StudentStatusBadge from '../StudentStatusBadge';
import type { StudentsTableRow, StudentsTableVariantModule } from './types';

export const studentColumn: OrderableActivityTableColumn<StudentsTableRow> = {
  field: 'display_name',
  label: 'Student',
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
    {
      field: 'last_activity',
      label: 'Last Activity',
      initialOrderDirection: 'descending',
    },
  ];

/**
 * Flatten every metric of a student into a single row.
 *
 * Shared with the auto-grading variant, which displays the same metrics plus a
 * grade. `auto_grading_grade` is absent for a plain assignment, so spreading it
 * is a no-op there.
 */
export function buildRows(students: StudentWithMetrics[]): StudentsTableRow[] {
  return students.map(
    ({ annotation_metrics, auto_grading_grade, ...rest }) => ({
      ...auto_grading_grade,
      ...annotation_metrics,
      ...rest,
    }),
  );
}

/**
 * Render the fields every variant displaying {@link StudentsTableRow} has in
 * common.
 *
 * A field with no renderer of its own is rendered as empty, so that a column
 * this variant does not know about never breaks the table.
 */
export function renderPlainField(
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

/**
 * Annotation metrics only: the table of an assignment without any grading
 * capability.
 *
 * This is the fallback of the registry: it handles every assignment no other
 * variant claims, so it has nothing to match on.
 */
export const plainVariant: StudentsTableVariantModule = {
  variant: 'plain',
  buildRows,
  columns: () => [studentColumn, ...metricsColumns],
  renderItem: renderPlainField,
};
