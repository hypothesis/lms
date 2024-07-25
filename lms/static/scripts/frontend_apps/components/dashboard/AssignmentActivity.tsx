import { useMemo } from 'preact/hooks';
import { useParams } from 'wouter-preact';

import type { AssignmentWithMetrics, StudentsResponse } from '../../api-types';
import { useConfig } from '../../config';
import { urlPath, useAPIFetch } from '../../utils/api';
import { useDocumentTitle } from '../../utils/hooks';
import { replaceURLParams } from '../../utils/url';
import DashboardBreadcrumbs from './DashboardBreadcrumbs';
import FormattedDate from './FormattedDate';
import OrderableActivityTable from './OrderableActivityTable';

type StudentsTableRow = {
  lms_id: string;
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
  const assignment = useAPIFetch<AssignmentWithMetrics>(
    replaceURLParams(routes.assignment, { assignment_id: assignmentId }),
  );
  const students = useAPIFetch<StudentsResponse>(routes.students_metrics, {
    assignment_id: assignmentId,
  });

  const title = `Assignment: ${assignment.data?.title}`;
  const rows: StudentsTableRow[] = useMemo(
    () =>
      (students.data?.students ?? []).map(
        ({ lms_id, display_name, annotation_metrics }) => ({
          lms_id,
          display_name,
          ...annotation_metrics,
        }),
      ),
    [students.data],
  );

  useDocumentTitle(assignment.data?.title ?? 'Untitled assignment');

  return (
    <div className="flex flex-col gap-y-5">
      <div>
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
        <h2 className="text-lg text-brand font-semibold" data-testid="title">
          {assignment.isLoading && 'Loading...'}
          {assignment.error && 'Could not load assignment title'}
          {assignment.data && title}
        </h2>
      </div>
      <OrderableActivityTable
        loading={students.isLoading}
        title={assignment.isLoading ? 'Loading...' : title}
        emptyMessage={
          students.error ? 'Could not load students' : 'No students found'
        }
        rows={rows}
        columns={[
          {
            field: 'display_name',
            label: 'Student',
          },
          {
            field: 'annotations',
            label: 'Annotations',
            initialOrderDirection: 'descending',
          },
          {
            field: 'replies',
            label: 'Replies',
            initialOrderDirection: 'descending',
          },
          {
            field: 'last_activity',
            label: 'Last Activity',
            initialOrderDirection: 'descending',
          },
        ]}
        defaultOrderField="display_name"
        renderItem={(stats, field) => {
          switch (field) {
            case 'annotations':
            case 'replies':
              return <div className="text-right">{stats[field]}</div>;
            case 'last_activity':
              return stats.last_activity ? (
                <FormattedDate date={stats.last_activity} />
              ) : (
                ''
              );
            case 'display_name':
              return (
                stats.display_name ?? (
                  <span className="flex flex-col gap-1.5">
                    <span className="italic">Unknown</span>
                    <span className="text-xs text-grey-7">
                      This student launched the assignment but didn{"'"}t
                      annotate yet
                    </span>
                  </span>
                )
              );
            default:
              return '';
          }
        }}
      />
    </div>
  );
}
