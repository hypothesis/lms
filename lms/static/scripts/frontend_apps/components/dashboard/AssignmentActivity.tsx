import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useMemo } from 'preact/hooks';
import { useParams } from 'wouter-preact';

import type { Assignment, StudentsResponse } from '../../api-types';
import { useConfig } from '../../config';
import { urlPath, useAPIFetch } from '../../utils/api';
import { formatDateTime } from '../../utils/date';
import { replaceURLParams } from '../../utils/url';
import DashboardBreadcrumbs from './DashboardBreadcrumbs';
import OrderableActivityTable from './OrderableActivityTable';

type StudentsTableRow = {
  id: string;
  display_name: string | null;
  last_activity: string | null;
  annotations: number;
  replies: number;
};

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
  const students = useAPIFetch<StudentsResponse>(
    replaceURLParams(routes.assignment_stats, { assignment_id: assignmentId }),
  );

  const title = `Assignment: ${assignment.data?.title}`;
  const rows: StudentsTableRow[] = useMemo(
    () =>
      (students.data?.students ?? []).map(
        ({ id, display_name, annotation_metrics }) => ({
          id,
          display_name,
          ...annotation_metrics,
        }),
      ),
    [students.data],
  );

  return (
    <Card>
      <CardHeader
        fullWidth
        classes={classnames(
          // Overwrite gap-x-2 and items-center from CardHeader
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
          rows={rows}
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
              : stats[field] ?? `Student ${stats.id.substring(0, 10)}`;
          }}
        />
      </CardContent>
    </Card>
  );
}
