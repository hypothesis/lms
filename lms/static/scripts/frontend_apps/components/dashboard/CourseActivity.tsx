import { Link } from '@hypothesis/frontend-shared';
import { useCallback, useMemo } from 'preact/hooks';
import {
  Link as RouterLink,
  useLocation,
  useParams,
  useSearch,
} from 'wouter-preact';

import type { AssignmentsResponse, Course } from '../../api-types';
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
  const [, navigate] = useLocation();
  const { dashboard } = useConfig(['dashboard']);
  const { routes } = dashboard;

  const { filters, updateFilters } = useDashboardFilters();
  const { assignmentIds, studentIds } = filters;
  const search = useSearch();
  const hasSelection = assignmentIds.length > 0 || studentIds.length > 0;
  const onClearSelection = useCallback(
    // Clear every filter but courses
    () => updateFilters({ studentIds: [], assignmentIds: [] }),
    [updateFilters],
  );

  const course = useAPIFetch<Course>(
    replaceURLParams(routes.course, { course_id: courseId }),
  );
  const assignments = useAPIFetch<AssignmentsResponse>(
    replaceURLParams(routes.course_assignments_metrics, {
      course_id: courseId,
    }),
    {
      assignment_id: assignmentIds,
      h_userid: studentIds,
      public_id: dashboard.organization_public_id,
    },
  );

  const rows: AssignmentsTableRow[] = useMemo(
    () =>
      (assignments.data?.assignments ?? []).map(
        ({ id, title, annotation_metrics }) => ({
          id,
          title,
          ...annotation_metrics,
        }),
      ),
    [assignments.data],
  );

  const title = course.data?.title ?? 'Untitled course';
  useDocumentTitle(title);

  return (
    <div className="flex flex-col gap-y-5">
      <div>
        <div className="mb-3 mt-1 w-full">
          <DashboardBreadcrumbs />
        </div>
        <h2 className="text-lg text-brand font-semibold" data-testid="title">
          {course.isLoading && 'Loading...'}
          {course.error && 'Could not load course title'}
          {course.data && title}
        </h2>
      </div>
      <DashboardActivityFilters
        selectedCourseIds={[courseId]}
        onCoursesChange={newCourseIds => {
          // When no courses are selected (which happens if either "All courses" is
          // selected or the active course is deselected), navigate to "All courses"
          // section and propagate the rest of the filters.
          if (newCourseIds.length === 0) {
            navigate(`?${search}`);
          }

          // When a course other than the "active" one (the one represented
          // in the URL) is selected, navigate to that course and propagate
          // the rest of the filters.
          const firstDifferentCourse = newCourseIds.find(c => c !== courseId);
          if (firstDifferentCourse) {
            navigate(`${courseURL(firstDifferentCourse)}?${search}`);
          }
        }}
        selectedAssignmentIds={assignmentIds}
        onAssignmentsChange={assignmentIds => updateFilters({ assignmentIds })}
        selectedStudentIds={studentIds}
        onStudentsChange={studentIds => updateFilters({ studentIds })}
        onClearSelection={hasSelection ? onClearSelection : undefined}
      />
      <OrderableActivityTable
        loading={assignments.isLoading}
        title={course.isLoading ? 'Loading...' : title}
        emptyMessage={
          assignments.error
            ? 'Could not load assignments'
            : 'No assignments found'
        }
        rows={rows}
        columns={[
          {
            field: 'title',
            label: 'Assignment',
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
            stats.last_activity && <FormattedDate date={stats.last_activity} />
          );
        }}
        navigateOnConfirmRow={stats => assignmentURL(stats.id)}
      />
    </div>
  );
}
