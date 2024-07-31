import { useCallback, useMemo } from 'preact/hooks';
import { useLocation, useParams, useSearch } from 'wouter-preact';

import type { AssignmentWithMetrics, StudentsResponse } from '../../api-types';
import { useConfig } from '../../config';
import { useAPIFetch } from '../../utils/api';
import { useDashboardFilters } from '../../utils/dashboard/hooks';
import { assignmentURL, courseURL } from '../../utils/dashboard/navigation';
import { useDocumentTitle } from '../../utils/hooks';
import { replaceURLParams } from '../../utils/url';
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
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const [, navigate] = useLocation();

  const { filters, updateFilters } = useDashboardFilters();
  const { studentIds } = filters;
  const search = useSearch();
  const onClearSelection = useCallback(
    // Clear student filters
    () => updateFilters({ studentIds: [] }),
    [updateFilters],
  );

  const assignment = useAPIFetch<AssignmentWithMetrics>(
    replaceURLParams(routes.assignment, { assignment_id: assignmentId }),
  );
  const students = useAPIFetch<StudentsResponse>(routes.students_metrics, {
    assignment_id: assignmentId,
    h_userid: studentIds,
    public_id: dashboard.organization_public_id,
  });
  const courseId = assignment.data && `${assignment.data.course.id}`;

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
                  href: courseURL(assignment.data.course.id),
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
      <DashboardActivityFilters
        selectedCourseIds={courseId ? [courseId] : []}
        onCoursesChange={newCourseIds => {
          // When no courses are selected (which happens if either "All courses" is
          // selected or the active course is deselected), navigate to "All courses"
          // section and propagate the rest of the filters.
          if (newCourseIds.length === 0) {
            navigate(
              search
                ? `?${search}&assignment_id=${assignmentId}`
                : `?assignment_id=${assignmentId}`,
            );
          }

          // When a course other than the "active" one (the one represented
          // in the URL) is selected, navigate to that course and propagate
          // the rest of the filters.
          const firstDifferentCourse = newCourseIds.find(c => c !== courseId);
          if (firstDifferentCourse) {
            navigate(
              `${courseURL(firstDifferentCourse)}?${search}&assignment_id=${assignmentId}`,
            );
          }
        }}
        selectedAssignmentIds={[assignmentId]}
        onAssignmentsChange={newAssignmentIds => {
          // When no assignments are selected (which happens if either "All
          // assignments" is selected or the active assignment is deselected),
          // navigate to "The assignment's course" section and propagate the
          // rest of the filters.
          if (newAssignmentIds.length === 0 && courseId) {
            navigate(`${courseURL(courseId)}?${search}`);
          }

          // When an assignment other than the "active" one (the one represented
          // in the URL) is selected, navigate to that assignment and propagate
          // the rest of the filters.
          const firstDifferentAssignment = newAssignmentIds.find(
            a => a !== assignmentId,
          );
          if (firstDifferentAssignment) {
            navigate(`${assignmentURL(firstDifferentAssignment)}?${search}`);
          }
        }}
        selectedStudentIds={studentIds}
        onStudentsChange={studentIds => updateFilters({ studentIds })}
        onClearSelection={studentIds.length > 0 ? onClearSelection : undefined}
      />
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
