import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Link,
} from '@hypothesis/frontend-shared';
import { useMemo } from 'preact/hooks';
import { useParams, Link as RouterLink } from 'wouter-preact';

import type { AssignmentsStats, Course } from '../../api-types';
import { useConfig } from '../../config';
import { useAPIFetch } from '../../utils/api';
import { formatDateTime } from '../../utils/date';
import { replaceURLParams } from '../../utils/url';
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
  const assignments = useAPIFetch<AssignmentsStats>(
    replaceURLParams(routes.course_assignment_stats, {
      course_id: courseId,
    }),
  );

  const rows: AssignmentsTableRow[] = useMemo(
    () =>
      (assignments.data ?? []).map(({ id, title, stats }) => ({
        id,
        title,
        ...stats,
      })),
    [assignments.data],
  );

  return (
    <Card>
      <CardHeader fullWidth>
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
                <RouterLink href={`/assignment/${stats.id}`} asChild>
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
