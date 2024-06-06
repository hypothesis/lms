import {
  Card,
  CardContent,
  CardHeader,
  Link,
} from '@hypothesis/frontend-shared';
import { Link as RouterLink } from 'wouter-preact';

import type { CoursesResponse } from '../../api-types';
import { useConfig } from '../../config';
import { urlPath, useAPIFetch } from '../../utils/api';
import { replaceURLParams } from '../../utils/url';
import OrderableActivityTable from './OrderableActivityTable';

export type OrganizationActivityProps = {
  organizationPublicId: string;
};

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

  return (
    <Card>
      <CardHeader title="Home" fullWidth />
      <CardContent>
        <OrderableActivityTable
          loading={courses.isLoading}
          title="Courses"
          emptyMessage={
            courses.error ? 'Could not load courses' : 'No courses found'
          }
          rows={courses.data?.courses ?? []}
          columnNames={{ title: 'Course Title' }}
          defaultOrderField="title"
          renderItem={stats => (
            <RouterLink href={urlPath`/courses/${String(stats.id)}`} asChild>
              <Link underline="always" variant="text">
                {stats.title}
              </Link>
            </RouterLink>
          )}
          navigateTo={stats => urlPath`/courses/${String(stats.id)}`}
        />
      </CardContent>
    </Card>
  );
}
