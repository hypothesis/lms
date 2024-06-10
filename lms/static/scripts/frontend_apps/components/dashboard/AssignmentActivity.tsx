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
import type { ConfigObject } from '../../config';
import { useConfig } from '../../config';
import { apiCall, urlPath } from '../../utils/api';
import { formatDateTime } from '../../utils/date';
import { useFetch } from '../../utils/fetch';
import { replaceURLParams } from '../../utils/url';
import DashboardBreadcrumbs from './DashboardBreadcrumbs';
import OrderableActivityTable from './OrderableActivityTable';

export function loader({
  config: { dashboard, api },
  params: { assignmentId },
  signal,
}: {
  config: ConfigObject;
  params: Record<string, string>;
  signal?: AbortSignal;
}) {
  if (!dashboard || !api) {
    throw new Error('Missing config!'); // TODO Handle this
  }

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
  loadResult?: AssignmentActivityLoadResult;
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
  loadResult,
}: AssignmentActivityProps) {
  const config = useConfig(['dashboard', 'api']);
  const params = useParams<{ assignmentId: string }>();

  const loaderResult = useFetch<AssignmentActivityLoadResult>(
    'assignment',
    async signal => {
      if (loadResult) {
        return loadResult;
      }

      return loader({ config, params, signal });
    },
  );

  const title = `Assignment: ${loaderResult.data?.assignment.title}`;
  const rows: StudentsTableRow[] = useMemo(
    () =>
      (loaderResult.data?.students.students ?? []).map(
        ({ id, display_name, annotation_metrics }) => ({
          id,
          display_name,
          ...annotation_metrics,
        }),
      ),
    [loaderResult.data],
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
        {loaderResult.data && (
          <div className="mb-3 mt-1 w-full">
            <DashboardBreadcrumbs
              links={[
                {
                  title: loaderResult.data.assignment.course.title,
                  href: urlPath`/courses/${String(loaderResult.data.assignment.course.id)}`,
                },
              ]}
            />
          </div>
        )}
        <CardTitle tagName="h2" data-testid="title">
          {loaderResult.isLoading && 'Loading...'}
          {loaderResult.error && 'Could not load assignment title'}
          {loaderResult.data && title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <OrderableActivityTable
          loading={loaderResult.isLoading}
          title={loaderResult.isLoading ? 'Loading...' : title}
          emptyMessage={
            loaderResult.error ? 'Could not load students' : 'No students found'
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
