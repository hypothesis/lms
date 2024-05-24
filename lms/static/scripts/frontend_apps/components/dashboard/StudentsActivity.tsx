import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@hypothesis/frontend-shared';
import { useParams } from 'wouter-preact';

import type { Assignment, StudentsStats } from '../../api-types';
import { useConfig } from '../../config';
import { useAPIFetch } from '../../utils/api';
import { formatDateTime } from '../../utils/date';
import { replaceURLParams } from '../../utils/url';
import OrderableActivityTable from './OrderableActivityTable';

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

  return (
    <Card>
      <CardHeader fullWidth>
        <CardTitle tagName="h2" data-testid="title">
          {assignment.isLoading && 'Loading...'}
          {assignment.error && 'Could not load assignment title'}
          {assignment.data && title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <OrderableActivityTable
          loading={students.isLoading}
          title={assignment.isLoading ? 'Loading...' : title}
          emptyMessage={
            students.error ? 'Could not load students' : 'No students found'
          }
          rows={students.data ?? []}
          columnNames={{
            display_name: 'Student',
            annotations: 'Annotations',
            replies: 'Replies',
            last_activity: 'Last Activity',
          }}
          defaultOrderField="display_name"
          renderItem={(stats, field) => {
            if (['annotations', 'replies'].includes(field)) {
              return <div className="text-right">{stats[field]}</div>;
            }

            return field === 'last_activity' && stats.last_activity
              ? formatDateTime(new Date(stats.last_activity))
              : stats[field];
          }}
        />
      </CardContent>
    </Card>
  );
}
