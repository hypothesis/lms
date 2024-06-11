import {
  Card,
  CardContent,
  CardHeader,
  Link,
} from '@hypothesis/frontend-shared';
import { Link as RouterLink } from 'wouter-preact';

import type { CoursesResponse } from '../../api-types';
import { apiCall, urlPath } from '../../utils/api';
import { replaceURLParams } from '../../utils/url';
import type { LoaderOptions } from '../ComponentWithLoaderWrapper';
import OrderableActivityTable from './OrderableActivityTable';

export function loader({
  config: { dashboard, api },
  params: { organizationId },
  signal,
}: LoaderOptions) {
  const { routes } = dashboard;
  const { authToken } = api;

  return apiCall<CoursesResponse>({
    path: replaceURLParams(routes.organization_courses, {
      organization_public_id: organizationId,
    }),
    authToken,
    signal,
  });
}

export type OrganizationActivityLoadResult = Awaited<ReturnType<typeof loader>>;

export type OrganizationActivityProps = {
  loaderResult: OrganizationActivityLoadResult;
  params: { organizationId: string };
};

const courseURL = (id: number) => urlPath`/courses/${String(id)}`;

/**
 * List of courses that belong to a specific organization
 */
export default function OrganizationActivity({
  loaderResult,
}: OrganizationActivityProps) {
  return (
    <Card>
      <CardHeader title="Home" fullWidth />
      <CardContent>
        <OrderableActivityTable
          title="Courses"
          emptyMessage="No courses found"
          rows={loaderResult.courses}
          columnNames={{ title: 'Course Title' }}
          defaultOrderField="title"
          renderItem={stats => (
            <RouterLink href={courseURL(stats.id)} asChild>
              <Link underline="always" variant="text">
                {stats.title}
              </Link>
            </RouterLink>
          )}
          navigateOnConfirmRow={stats => courseURL(stats.id)}
        />
      </CardContent>
    </Card>
  );
}
