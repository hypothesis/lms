import { useMemo } from 'preact/hooks';
import { useLocation, useParams, useSearch } from 'wouter-preact';

import type {
  AssignmentWithCourse,
  StudentsMetricsResponse,
} from '../../api-types';
import { useConfig } from '../../config';
import { urlPath, useAPIFetch } from '../../utils/api';
import { useDashboardFilters } from '../../utils/dashboard/hooks';
import { courseURL } from '../../utils/dashboard/navigation';
import { useDocumentTitle } from '../../utils/hooks';
import { recordToQueryString, replaceURLParams } from '../../utils/url';
import DashboardActivityFilters from './DashboardActivityFilters';
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
  const { assignmentId, organizationPublicId } = useParams<{
    assignmentId: string;
    organizationPublicId?: string;
  }>();

  const { filters, updateFilters } = useDashboardFilters();
  const { studentIds } = filters;
  const search = useSearch();
  const [, navigate] = useLocation();

  const assignment = useAPIFetch<AssignmentWithCourse>(
    replaceURLParams(routes.assignment, { assignment_id: assignmentId }),
  );

  const students = useAPIFetch<StudentsMetricsResponse>(
    routes.students_metrics,
    {
      h_userid: studentIds,
      assignment_id: assignmentId,
      org_public_id: organizationPublicId,
    },
  );

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

  const title = assignment.data?.title ?? 'Untitled assignment';
  useDocumentTitle(title);

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
      {assignment.data && (
        <DashboardActivityFilters
          courses={{
            activeItem: assignment.data.course,
            // When the active course is cleared, navigate to home, but keep
            // active assignment and students
            onClear: () =>
              navigate(
                recordToQueryString({
                  student_id: studentIds,
                  assignment_id: assignmentId,
                }),
              ),
          }}
          assignments={{
            activeItem: assignment.data,
            // When active assignment is cleared, navigate to its course page,
            // but keep other query params intact
            onClear: () => {
              const query = search.length === 0 ? '' : `?${search}`;
              navigate(`${courseURL(assignment.data!.course.id)}${query}`);
            },
          }}
          students={{
            selectedIds: studentIds,
            onChange: studentIds => updateFilters({ studentIds }),
          }}
          onClearSelection={
            studentIds.length > 0
              ? () => updateFilters({ studentIds: [] })
              : undefined
          }
        />
      )}
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
