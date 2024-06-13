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
import { replaceURLParams } from '../../utils/url';
import type { LoaderOptions } from '../ComponentWithLoaderWrapper';
import DashboardBreadcrumbs from './DashboardBreadcrumbs';
import OrderableActivityTable from './OrderableActivityTable';

export function loader({
  config: { dashboard, api },
  params: { assignmentId },
  signal,
}: LoaderOptions) {
  const { routes } = dashboard;
  const { authToken } = api;

  return Promise.all([
    apiCall<Assignment>({
      path: replaceURLParams(routes.assignment, {
        assignment_id: assignmentId,
      }),
      authToken,
      signal,
    }),
    apiCall<StudentsResponse>({
      path: replaceURLParams(routes.assignment_stats, {
        assignment_id: assignmentId,
      }),
      authToken,
      signal,
    }),
  ]).then(([assignment, students]) => ({ assignment, students }));
}

export type AssignmentActivityLoadResult = Awaited<ReturnType<typeof loader>>;

export type AssignmentActivityProps = {
  loaderResult: AssignmentActivityLoadResult;
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
}: AssignmentActivityProps) {
  const title = `Assignment: ${loaderResult.assignment.title}`;
  const rows: StudentsTableRow[] = useMemo(
    () =>
      loaderResult.students.students.map(
        ({ id, display_name, annotation_metrics }) => ({
          id,
          display_name,
          ...annotation_metrics,
        }),
      ),
    [loaderResult.students.students],
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
          <DashboardBreadcrumbs
            links={[
              {
                title: loaderResult.assignment.course.title,
                href: urlPath`/courses/${String(loaderResult.assignment.course.id)}`,
              },
            ]}
          />
        </div>
        <CardTitle tagName="h2" data-testid="title">
          title
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
