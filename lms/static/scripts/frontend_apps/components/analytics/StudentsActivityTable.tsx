import { Card, CardContent, DataTable } from '@hypothesis/frontend-shared';

type AssignmentInfo = {
  id: string;
  name: string;
};

type StudentStats = {
  name: string;
  lastActivity: string;
  annotations: number;
  replies: number;
};

export type StudentsActivityTableProps = {
  assignment: AssignmentInfo | null;
  students: StudentStats[];
  loading?: boolean;
};

export default function StudentsActivityTable({
  assignment,
  students,
  loading,
}: StudentsActivityTableProps) {
  const title = assignment
    ? `Student activity for assignment ${assignment.name}`
    : 'Loading assignment info...';

  return (
    <Card>
      <CardContent>
        <h2 className="text-brand mb-3 text-xl">{title}</h2>
        <DataTable
          title={title}
          columns={[
            { field: 'name', label: 'Name', classes: 'w-[70%]' },
            {
              field: 'annotations',
              label: 'Annotations',
              classes: 'text-right',
            },
            { field: 'replies', label: 'Replies', classes: 'text-right' },
            {
              field: 'lastActivity',
              label: 'Last Activity',
              classes: 'text-right',
            },
          ]}
          rows={students}
          renderItem={(r, field) =>
            field === 'name' ? (
              r[field]
            ) : (
              <div className="text-right">{r[field]}</div>
            )
          }
          loading={loading}
        />
      </CardContent>
    </Card>
  );
}
