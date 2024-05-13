import {
  Card,
  CardContent,
  DataTable,
  useOrderedRows,
} from '@hypothesis/frontend-shared';
import type { DataTableProps } from '@hypothesis/frontend-shared';
import { useState } from 'preact/hooks';
import { useParams } from 'wouter-preact';

import type { APIAssignment, StudentStats } from '../../api-types';
import { useConfig } from '../../config';
import { useAPIFetch } from '../../utils/api';
import { formatDateTime } from '../../utils/date';

type MandatoryOrder<T> = NonNullable<DataTableProps<T>['order']>;

export default function StudentsActivity() {
  const { dashboard } = useConfig(['dashboard']);
  const { links: routes } = dashboard;
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const assignment = useAPIFetch<APIAssignment>(
    routes.assignmentApi.replace(':id_', assignmentId),
  );
  const students = useAPIFetch<StudentStats[]>(
    routes.assignmentStatsApi.replace(':id_', assignmentId),
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
          {title}
        </h2>
        <DataTable
          grid
          striped={false}
          emptyMessage="No students found"
          title={assignment.isLoading ? 'Loading...' : title}
          columns={[
            { field: 'display_name', label: 'Name', classes: 'w-[60%]' },
            { field: 'annotations', label: 'Annotations' },
            { field: 'replies', label: 'Replies' },
            { field: 'last_activity', label: 'Last Activity' },
          ]}
          rows={orderedStudents}
          renderItem={(stats, field) => {
            if (['annotations', 'replies'].includes(field)) {
              return <div className="text-right">{stats[field]}</div>;
            }

            return field === 'last_activity' && stats[field]
              ? formatDateTime(new Date(stats[field]))
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
