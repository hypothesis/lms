import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useMemo } from 'preact/hooks';

import type { Assignment, StudentsResponse } from '../../api-types';
import { apiCall, urlPath } from '../../utils/api';
import { formatDateTime } from '../../utils/date';
import { useFetch } from '../../utils/fetch';
import { replaceURLParams } from '../../utils/url';
import type { RouteModule } from '../ComponentWithLoaderWrapper';
import DashboardBreadcrumbs from './DashboardBreadcrumbs';
import OrderableActivityTable from './OrderableActivityTable';

export const loader: RouteModule['loader'] = ({
  config: { dashboard, api },
  params: { assignmentId },
  signal,
}) => {
  const { routes } = dashboard;
  const { authToken } = api;

  return {
    awaitable: apiCall<StudentsResponse>({
      path: replaceURLParams(routes.assignment_stats, {
        assignment_id: assignmentId,
      }),
      authToken,
      signal,
    }),
    rest: {
      assignment: apiCall<Assignment>({
        path: replaceURLParams(routes.assignment, {
          assignment_id: assignmentId,
        }),
        authToken,
        signal,
      }),
    },
  };
};

export type AssignmentActivityProps = {
  loaderResult: StudentsResponse;
  assignment: Promise<Assignment>;
};

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
export default function AssignmentActivity({
  loaderResult,
  assignment,
}: AssignmentActivityProps) {
  const assignmentLoader = useFetch('assignment', () => assignment);
  const title = `Assignment: ${assignmentLoader.data?.title}`;
  const rows: StudentsTableRow[] = useMemo(
    () =>
      loaderResult.students.map(({ id, display_name, annotation_metrics }) => ({
        id,
        display_name,
        ...annotation_metrics,
      })),
    [loaderResult.students],
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
        {assignmentLoader.data && (
          <div className="mb-3 mt-1 w-full">
            <DashboardBreadcrumbs
              links={[
                {
                  title: assignmentLoader.data.course.title,
                  href: urlPath`/courses/${String(assignmentLoader.data.course.id)}`,
                },
              ]}
            />
          </div>
        )}
        <CardTitle tagName="h2" data-testid="title">
          {assignmentLoader.isLoading && 'Loading...'}
          {assignmentLoader.error && 'Could not load assignment title'}
          {assignmentLoader.data && title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <OrderableActivityTable
          title={title}
          emptyMessage=""
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
            } else if (field === 'last_activity') {
              return stats.last_activity
                ? formatDateTime(new Date(stats.last_activity))
                : '';
            }

            return stats[field] ?? `Student ${stats.id.substring(0, 10)}`;
          }}
        />
      </CardContent>
    </Card>
  );
}
