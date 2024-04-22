import {
  Card,
  CardContent,
  DataTable,
  useOrderedRows,
} from '@hypothesis/frontend-shared';
import type { DataTableProps } from '@hypothesis/frontend-shared';
import { useState } from 'preact/hooks';

import type { StudentStats } from '../../api-types';
import { formatDateTime } from '../../utils/date';

export type AssignmentInfo = {
  title: string;
};

export type StudentsActivityTableProps = {
  assignment: AssignmentInfo;
  students: StudentStats[];
  loading?: boolean;
};

type MandatoryOrder<T> = NonNullable<DataTableProps<T>['order']>;

export default function StudentsActivityTable({
  assignment,
  students,
  loading,
}: StudentsActivityTableProps) {
  const title = `Student activity for assignment "${assignment.title}"`;
  const [order, setOrder] = useState<MandatoryOrder<StudentStats>>({
    field: 'display_name',
    direction: 'ascending',
  });
  const orderedStudents = useOrderedRows(students, order);

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
          title={title}
          columns={[
            { field: 'display_name', label: 'Name', classes: 'w-[60%]' },
            {
              field: 'annotations',
              label: 'Annotations',
              classes: 'text-right',
            },
            { field: 'replies', label: 'Replies', classes: 'text-right' },
            {
              field: 'last_activity',
              label: 'Last Activity',
              classes: 'text-right',
            },
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
          loading={loading}
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
