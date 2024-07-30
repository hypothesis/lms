import { Link } from '@hypothesis/frontend-shared';
import { useMemo } from 'preact/hooks';
import { Link as RouterLink } from 'wouter-preact';

import type { CoursesResponse } from '../../api-types';
import { useConfig } from '../../config';
import { urlPath, useAPIFetch } from '../../utils/api';
import { useDashboardFilters } from '../../utils/dashboard/hooks';
import { useDocumentTitle } from '../../utils/hooks';
import DashboardActivityFilters from './DashboardActivityFilters';
import FormattedDate from './FormattedDate';
import OrderableActivityTable from './OrderableActivityTable';

type CoursesTableRow = {
  id: number;
  title: string;
  assignments: number;
  last_launched: string | null;
};

const courseURL = (id: number) => urlPath`/courses/${String(id)}`;

/**
 * List of courses that belong to a specific organization
 */
export default function OrganizationActivity() {
  const { dashboard } = useConfig(['dashboard']);
  const { routes } = dashboard;

  useDocumentTitle('All courses');

  const { filters, updateFilters } = useDashboardFilters();
  const { courseIds, assignmentIds, studentIds } = filters;

  const courses = useAPIFetch<CoursesResponse>(routes.courses_metrics, {
    h_userid: studentIds,
    assignment_id: assignmentIds,
    course_id: courseIds,
    public_id: dashboard.organization_public_id,
  });
  const rows: CoursesTableRow[] = useMemo(
    () =>
      courses.data?.courses.map(({ id, title, course_metrics }) => ({
        id,
        title,
        ...course_metrics,
      })) ?? [],
    [courses.data],
  );

  return (
    <div className="flex flex-col gap-y-5">
      <h2 className="text-lg text-brand font-semibold">All courses</h2>
      <DashboardActivityFilters
        selectedStudentIds={studentIds}
        onStudentsChange={studentIds => updateFilters({ studentIds })}
        selectedAssignmentIds={assignmentIds}
        onAssignmentsChange={assignmentIds => updateFilters({ assignmentIds })}
        selectedCourseIds={courseIds}
        onCoursesChange={courseIds => updateFilters({ courseIds })}
        onClearSelection={() =>
          updateFilters({ studentIds: [], assignmentIds: [], courseIds: [] })
        }
      />
      <OrderableActivityTable
        loading={courses.isLoading}
        title="Courses"
        emptyMessage={
          courses.error ? 'Could not load courses' : 'No courses found'
        }
        rows={rows}
        columns={[
          {
            field: 'title',
            label: 'Course title',
          },
          {
            field: 'assignments',
            label: 'Assignments',
            initialOrderDirection: 'descending',
          },
          {
            field: 'last_launched',
            label: 'Last launched',
            initialOrderDirection: 'descending',
          },
        ]}
        defaultOrderField="title"
        renderItem={(stats, field) => {
          if (field === 'assignments') {
            return <div className="text-right">{stats[field]}</div>;
          } else if (field === 'last_launched') {
            return stats.last_launched ? (
              <FormattedDate date={stats.last_launched} />
            ) : (
              ''
            );
          }

          return (
            <RouterLink href={urlPath`/courses/${String(stats.id)}`} asChild>
              <Link underline="always" variant="text">
                {stats.title}
              </Link>
            </RouterLink>
          );
        }}
        navigateOnConfirmRow={stats => courseURL(stats.id)}
      />
    </div>
  );
}
