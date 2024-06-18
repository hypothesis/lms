import { Link } from '@hypothesis/frontend-shared';
import { useMemo } from 'preact/hooks';
import { Link as RouterLink } from 'wouter-preact';

import type { CoursesResponse } from '../../api-types';
import { useConfig } from '../../config';
import { urlPath, useAPIFetch } from '../../utils/api';
import { formatDateTime } from '../../utils/date';
import { replaceURLParams } from '../../utils/url';
import OrderableActivityTable from './OrderableActivityTable';

export type OrganizationActivityProps = {
  organizationPublicId: string;
};

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
export default function OrganizationActivity({
  organizationPublicId,
}: OrganizationActivityProps) {
  const { dashboard } = useConfig(['dashboard']);
  const { routes } = dashboard;
  const courses = useAPIFetch<CoursesResponse>(
    replaceURLParams(routes.organization_courses, {
      organization_public_id: organizationPublicId,
    }),
  );
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
      <OrderableActivityTable
        loading={courses.isLoading}
        title="Courses"
        emptyMessage={
          courses.error ? 'Could not load courses' : 'No courses found'
        }
        rows={rows}
        columnNames={{
          title: 'Course Title',
          assignments: 'Assignments',
          last_launched: 'Last launched',
        }}
        defaultOrderField="title"
        renderItem={(stats, field) => {
          if (field === 'assignments') {
            return <div className="text-right">{stats[field]}</div>;
          } else if (field === 'last_launched') {
            return stats.last_launched
              ? formatDateTime(new Date(stats.last_launched))
              : '';
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
