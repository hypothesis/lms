import {
  Card,
  CardContent,
  DataTable,
  useOrderedRows,
} from '@hypothesis/frontend-shared';
import type { DataTableProps } from '@hypothesis/frontend-shared';
import { useState } from 'preact/hooks';

import type { StudentStats, AssignmentStats } from '../../api-types';
import { formatDateTime } from '../../utils/date';

export type AssignmentInfo = {
  title: string;
};

export type CourseInfo = {
  title: string;
};

export type StudentsActivityTableProps = {
  assignment: AssignmentInfo;
  students: StudentStats[];
  loading?: boolean;
};

type MandatoryOrder<T> = NonNullable<DataTableProps<T>['order']>;

export function StudentsActivityTable({
  assignment,
  students,
  loading,
}: StudentsActivityTableProps) {
  const title = `Assignment: ${assignment.title}`;
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

export type CourseAssignmentsTableProps = {
  course: CourseInfo;
  assignments: AssignmentStats[];
  loading?: boolean;
};

export function CourseAssignmentsTable({
  course,
  assignments,
  loading,
}: CourseAssignmentsTableProps) {
  const title = `Course: ${course.title}`;
  const [order, setOrder] = useState<MandatoryOrder<AssignmentStats>>({
    field: 'name',
    direction: 'ascending',
  });
  const orderedAssignments = useOrderedRows(assignments, order);

  return (
    <Card>
      <CardContent>
        <h2 className="text-brand mb-3 text-xl" data-testid="title">
          {title}
        </h2>
        <DataTable
          grid
          striped={false}
          emptyMessage="No assignments found"
          title={title}
          columns={[{ field: 'name', label: 'Name', classes: 'w-[60%]' }]}
          rows={orderedAssignments}
          renderItem={(stats, field) => {
            return stats[field];
          }}
          loading={loading}
          orderableColumns={['name']}
          order={order}
          onOrderChange={setOrder}
        />
      </CardContent>
    </Card>
  );
}
