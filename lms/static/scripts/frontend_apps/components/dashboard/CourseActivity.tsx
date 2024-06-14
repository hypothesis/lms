import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Link,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useMemo } from 'preact/hooks';
import { Link as RouterLink } from 'wouter-preact';

import type { AssignmentsResponse, Course } from '../../api-types';
import { apiCall, urlPath } from '../../utils/api';
import { formatDateTime } from '../../utils/date';
import { useFetch } from '../../utils/fetch';
import { replaceURLParams } from '../../utils/url';
import type { RouteModule } from '../ComponentWithLoaderWrapper';
import DashboardBreadcrumbs from './DashboardBreadcrumbs';
import OrderableActivityTable from './OrderableActivityTable';

export const loader: RouteModule['loader'] = ({
  config: { dashboard, api },
  params: { courseId },
  signal,
}) => {
  const { routes } = dashboard;
  const { authToken } = api;

  return {
    awaitable: apiCall<AssignmentsResponse>({
      path: replaceURLParams(routes.course_assignment_stats, {
        course_id: courseId,
      }),
      authToken,
      signal,
    }),
    rest: {
      course: apiCall<Course>({
        path: replaceURLParams(routes.course, { course_id: courseId }),
        authToken,
        signal,
      }),
    },
  };
};

export type CourseActivityProps = {
  loaderResult: AssignmentsResponse;
  course: Promise<Course>;
};

type AssignmentsTableRow = {
  id: number;
  title: string;
  last_activity: string | null;
  annotations: number;
  replies: number;
};

const assignmentURL = (id: number) => urlPath`/assignments/${String(id)}`;

/**
 * Activity in a list of assignments that are part of a specific course
 */
export default function CourseActivity({
  loaderResult,
  course,
}: CourseActivityProps) {
  const courseLoader = useFetch('course', () => course);
  const rows: AssignmentsTableRow[] = useMemo(
    () =>
      loaderResult.assignments.map(({ id, title, annotation_metrics }) => ({
        id,
        title,
        ...annotation_metrics,
      })),
    [loaderResult.assignments],
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
          {courseLoader.data?.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <OrderableActivityTable
          title={courseLoader.data?.title ?? ''}
          emptyMessage="No assignments found"
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
                <RouterLink href={assignmentURL(stats.id)} asChild>
                  <Link underline="always" variant="text">
                    {stats.title}
                  </Link>
                </RouterLink>
              );
            }

            return (
              stats.last_activity &&
              formatDateTime(new Date(stats.last_activity))
            );
          }}
          navigateOnConfirmRow={stats => assignmentURL(stats.id)}
        />
      </CardContent>
    </Card>
  );
}
