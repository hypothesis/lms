import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Link,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useMemo } from 'preact/hooks';
import { useParams, Link as RouterLink } from 'wouter-preact';

import type { AssignmentsResponse, Course } from '../../api-types';
import { useConfig } from '../../config';
import { urlPath, useAPIFetch } from '../../utils/api';
import { formatDateTime } from '../../utils/date';
import { replaceURLParams } from '../../utils/url';
import DashboardBreadcrumbs from './DashboardBreadcrumbs';
import OrderableActivityTable from './OrderableActivityTable';

type AssignmentsTableRow = {
  id: number;
  title: string;
  last_activity: string | null;
  annotations: number;
  replies: number;
};

/**
 * Activity in a list of assignments that are part of a specific course
 */
export default function CourseActivity() {
  const { courseId } = useParams<{ courseId: string }>();
  const { dashboard } = useConfig(['dashboard']);
  const { routes } = dashboard;
  const course = useAPIFetch<Course>(
    replaceURLParams(routes.course, { course_id: courseId }),
  );
  const assignments = useAPIFetch<AssignmentsResponse>(
    replaceURLParams(routes.course_assignment_stats, {
      course_id: courseId,
    }),
  );

  const rows: AssignmentsTableRow[] = useMemo(
    () =>
      (assignments.data?.assignments ?? []).map(({ id, title, stats }) => ({
        id,
        title,
        ...stats,
      })),
    [assignments.data],
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
        <div className="mb-3 mt-1 w-full">
          <DashboardBreadcrumbs />
        </div>
        <CardTitle tagName="h2" data-testid="title">
          {course.isLoading && 'Loading...'}
          {course.error && 'Could not load course title'}
          {course.data && course.data.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <OrderableActivityTable
          loading={assignments.isLoading}
          title={course.data?.title ?? 'Loading...'}
          emptyMessage={
            assignments.error
              ? 'Could not load assignments'
              : 'No assignments found'
          }
          rows={rows}
          columnNames={{
            title: 'Assignment',
            annotations: 'Annotations',
            replies: 'Replies',
            last_activity: 'Last Activity',
          }}
          defaultOrderField="title"
          renderItem={(stats, field) => {
            if (['annotations', 'replies'].includes(field)) {
              return <div className="text-right">{stats[field]}</div>;
            } else if (field === 'title') {
              return (
                <RouterLink
                  href={urlPath`/assignments/${String(stats.id)}`}
                  asChild
                >
                  <Link>{stats.title}</Link>
                </RouterLink>
              );
            }

            return (
              stats.last_activity &&
              formatDateTime(new Date(stats.last_activity))
            );
          }}
        />
      </CardContent>
    </Card>
  );
}
