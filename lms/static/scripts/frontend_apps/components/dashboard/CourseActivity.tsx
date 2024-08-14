import { Link } from '@hypothesis/frontend-shared';
import { useCallback, useMemo } from 'preact/hooks';
import {
  Link as RouterLink,
  useLocation,
  useParams,
  useSearch,
} from 'wouter-preact';

import type { AssignmentsMetricsResponse, Course } from '../../api-types';
import { useConfig } from '../../config';
import { useAPIFetch } from '../../utils/api';
import { useDashboardFilters } from '../../utils/dashboard/hooks';
import { assignmentURL } from '../../utils/dashboard/navigation';
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
  const { courseId, organizationPublicId } = useParams<{
    courseId: string;
    organizationPublicId?: string;
  }>();
  const [, navigate] = useLocation();
  const { dashboard } = useConfig(['dashboard']);
  const { routes } = dashboard;

  const { filters, updateFilters, urlWithFilters } = useDashboardFilters();
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
  const assignments = useAPIFetch<AssignmentsMetricsResponse>(
    replaceURLParams(routes.course_assignments_metrics, {
      course_id: courseId,
    }),
    {
      assignment_id: assignmentIds,
      h_userid: studentIds,
      org_public_id: organizationPublicId,
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
          <DashboardBreadcrumbs
            allCoursesLink={urlWithFilters(
              { assignmentIds, studentIds },
              { path: '/' },
            )}
          />
        </div>
        <h2 className="text-lg text-brand font-semibold" data-testid="title">
          {course.isLoading && 'Loading...'}
          {course.error && 'Could not load course title'}
          {course.data && title}
        </h2>
      </div>
      {course.data && (
        <DashboardActivityFilters
          courses={{
            activeItem: course.data,
            // When selected course is cleared, navigate to the home page,
            // AKA "All courses"
            onClear: () => navigate(search.length > 0 ? `/?${search}` : '/'),
          }}
          assignments={{
            selectedIds: assignmentIds,
            onChange: assignmentIds => updateFilters({ assignmentIds }),
          }}
          students={{
            selectedIds: studentIds,
            onChange: studentIds => updateFilters({ studentIds }),
          }}
          onClearSelection={hasSelection ? onClearSelection : undefined}
        />
      )}
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
              <RouterLink
                href={urlWithFilters(
                  { studentIds },
                  { path: assignmentURL(stats.id) },
                )}
                asChild
              >
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
        navigateOnConfirmRow={stats =>
          urlWithFilters({ studentIds }, { path: assignmentURL(stats.id) })
        }
      />
    </div>
  );
}
