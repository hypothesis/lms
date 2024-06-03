import { Card, CardContent, CardHeader } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useParams } from 'wouter-preact';

import type { Assignment, StudentsStats } from '../../api-types';
import { useConfig } from '../../config';
import { urlPath, useAPIFetch } from '../../utils/api';
import { formatDateTime } from '../../utils/date';
import { replaceURLParams } from '../../utils/url';
import DashboardBreadcrumbs from './DashboardBreadcrumbs';
import OrderableActivityTable from './OrderableActivityTable';

/**
 * Activity in a list of students that are part of a specific assignment
 */
export default function AssignmentActivity() {
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
      <CardHeader
        fullWidth
        classes={classnames(
          // Overwriting gap-x-2 and items-center from CardHeader
          'flex-col !gap-x-0 !items-start',
        )}
      >
        {assignment.data && (
          <div className="mb-3 mt-1 w-full">
            <DashboardBreadcrumbs
              links={[
                {
                  title: assignment.data.course.title,
                  href: urlPath`/courses/${String(assignment.data.course.id)}`,
                },
              ]}
            />
          </div>
        )}
        <h2 data-testid="title" className="text-lg text-brand font-semibold">
          {assignment.isLoading && 'Loading...'}
          {assignment.error && 'Could not load assignment title'}
          {assignment.data && title}
        </h2>
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
