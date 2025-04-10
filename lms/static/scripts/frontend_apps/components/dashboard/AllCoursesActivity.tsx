import { Link } from '@hypothesis/frontend-shared';
import { useMemo } from 'preact/hooks';
import { Link as RouterLink } from 'wouter-preact';
import { useParams } from 'wouter-preact';

import type { CoursesMetricsResponse } from '../../api-types';
import { useConfig } from '../../config';
import { useAPIFetch } from '../../utils/api';
import { useDashboardFilters } from '../../utils/dashboard/hooks';
import { courseURL } from '../../utils/dashboard/navigation';
import { rootViewTitle } from '../../utils/dashboard/root-view-title';
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

/**
 * List of courses that current user has access to in the dashboard
 */
export default function AllCoursesActivity() {
  const { dashboard } = useConfig(['dashboard']);
  const { routes } = dashboard;
  const title = rootViewTitle(dashboard);

  useDocumentTitle(title);

  const { organizationPublicId } = useParams();
  const { filters, updateFilters, urlWithFilters } = useDashboardFilters();
  const { courseIds, assignmentIds, studentIds } = filters;

  const courses = useAPIFetch<CoursesMetricsResponse>(routes.courses_metrics, {
    h_userid: studentIds,
    assignment_id: assignmentIds,
    course_id: courseIds,
    org_public_id: organizationPublicId,
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
      <h2 className="text-lg text-brand font-semibold" data-testid="title">
        {title}
      </h2>
      <DashboardActivityFilters
        students={{
          selectedIds: studentIds,
          onChange: studentIds => updateFilters({ studentIds }),
        }}
        assignments={{
          selectedIds: assignmentIds,
          onChange: assignmentIds => updateFilters({ assignmentIds }),
        }}
        courses={{
          selectedIds: courseIds,
          onChange: courseIds => updateFilters({ courseIds }),
        }}
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
            <RouterLink
              href={urlWithFilters(
                { assignmentIds, studentIds },
                { path: courseURL(stats.id) },
              )}
              asChild
            >
              <Link underline="always" variant="text">
                {stats.title}
              </Link>
            </RouterLink>
          );
        }}
        navigateOnConfirmRow={stats =>
          urlWithFilters(
            { assignmentIds, studentIds },
            { path: courseURL(stats.id) },
          )
        }
      />
    </div>
  );
}
