import {
  Card,
  CardContent,
  DataTable,
  useOrderedRows,
} from '@hypothesis/frontend-shared';
import type { DataTableProps } from '@hypothesis/frontend-shared';
import { useState } from 'preact/hooks';
import { useParams } from 'wouter-preact';

import type { Assignment, StudentsStats, StudentStats } from '../../api-types';
import { useConfig } from '../../config';
import { useAPIFetch } from '../../utils/api';
import { formatDateTime } from '../../utils/date';
import { replaceURLParams } from '../../utils/url';

type MandatoryOrder<T> = NonNullable<DataTableProps<T>['order']>;

/**
 * Activity in a list of students that are part of a specific assignment
 */
export default function StudentsActivity() {
  const { dashboard } = useConfig(['dashboard']);
  const { routes } = dashboard;
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const assignment = useAPIFetch<Assignment>(
    replaceURLParams(routes.assignment, { assignment_id: assignmentId }),
  );
  const students = useAPIFetch<StudentsStats>(
    replaceURLParams(routes.assignment_stats, { assignment_id: assignmentId }),
  );

  const title = `Assignment: ${assignment.data?.title}`;
  const [order, setOrder] = useState<MandatoryOrder<StudentStats>>({
    field: 'display_name',
    direction: 'ascending',
  });
  const orderedStudents = useOrderedRows(students.data ?? [], order);

  return (
    <Card>
      <CardContent>
        <h2 className="text-brand mb-3 text-xl" data-testid="title">
          {assignment.isLoading && 'Loading...'}
          {assignment.error && 'Could not load assignment title'}
          {assignment.data && title}
        </h2>
        <DataTable
          grid
          striped={false}
          emptyMessage={
            students.error ? 'Could not load students' : 'No students found'
          }
          title={assignment.isLoading ? 'Loading...' : title}
          rows={orderedStudents}
          columns={[
            { field: 'display_name', label: 'Student', classes: 'w-[60%]' },
            { field: 'annotations', label: 'Annotations' },
            { field: 'replies', label: 'Replies' },
            { field: 'last_activity', label: 'Last Activity' },
          ]}
          renderItem={(stats, field) => {
            if (['annotations', 'replies'].includes(field)) {
              return <div className="text-right">{stats[field]}</div>;
            }

            return field === 'last_activity' && stats.last_activity
              ? formatDateTime(new Date(stats.last_activity))
              : stats[field];
          }}
          loading={students.isLoading}
          orderableColumns={[
            'display_name',
            'annotations',
            'replies',
            'last_activity',
          ]}
          order={order}
          onOrderChange={setOrder}
        />
      </CardContent>
    </Card>
  );
}
