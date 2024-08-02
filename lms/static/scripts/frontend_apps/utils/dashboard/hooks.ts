import { useCallback, useMemo } from 'preact/hooks';
import { useLocation, useSearch } from 'wouter-preact';

import { queryStringToRecord, recordToQueryString } from '../url';

export type DashboardFilters = {
  studentIds: string[];
  assignmentIds: string[];
  courseIds: string[];
};

export type UseDashboardFilters = {
  filters: DashboardFilters;
  updateFilters: (filtersToUpdate: Partial<DashboardFilters>) => void;
};

/**
 * Hook used to read and update the state of the dashboard filters.
 *
 * The filter state is synchronized with query string parameters in the URL.
 */
export function useDashboardFilters(): UseDashboardFilters {
  const search = useSearch();
  const queryParams = useMemo(() => queryStringToRecord(search), [search]);
  const filters = useMemo(() => {
    const { student_id = [], course_id = [], assignment_id = [] } = queryParams;
    const courseIds = Array.isArray(course_id) ? course_id : [course_id];
    const assignmentIds = Array.isArray(assignment_id)
      ? assignment_id
      : [assignment_id];
    const studentIds = Array.isArray(student_id) ? student_id : [student_id];

    return { courseIds, assignmentIds, studentIds };
  }, [queryParams]);

  const [location, navigate] = useDashboardLocation();
  const updateFilters = useCallback(
    ({ courseIds, assignmentIds, studentIds }: Partial<DashboardFilters>) => {
      const newQueryParams = { ...queryParams };
      if (courseIds) {
        newQueryParams.course_id = courseIds;
      }
      if (assignmentIds) {
        newQueryParams.assignment_id = assignmentIds;
      }
      if (studentIds) {
        newQueryParams.student_id = studentIds;
      }

      // The router's base URL is represented in `location` as '/', even if
      // that URL does not actually end with `/` (eg. `/dashboard`).
      // When we update the query string, we want to avoid modifying the path.
      const normalizedLocation = location === '/' ? '' : location;

      navigate(`${normalizedLocation}${recordToQueryString(newQueryParams)}`, {
        replace: true,
      });
    },
    [location, navigate, queryParams],
  );

  return { filters, updateFilters };
}

/**
 * Given a new and current query strings, this checks if current one has
 * organization_public_id, and propagates it to the new one
 */
export function urlWithOrgPublicId(
  destinationURL: string | URL,
  currentQuery: string,
): URL {
  const url =
    typeof destinationURL === 'string'
      ? new URL(destinationURL)
      : destinationURL;
  const newQueryAsRecord = queryStringToRecord(url.search);
  const { public_id } = queryStringToRecord(currentQuery);

  // If there's an organization public ID in the query, make sure it is preserved
  // by merging it with provided URL's query
  // TODO Do not override public id if provided in new query
  url.search = recordToQueryString({
    ...newQueryAsRecord,
    public_id, // TODO Rename to organization_public_id
  });

  return url;
}

/**
 * A drop-in replacement for wouter's useLocation, except that the `navigate`
 * callback will always preserve the organization_public_id query param if
 * present
 */
export function useDashboardLocation(): ReturnType<typeof useLocation> {
  const [location, navigate] = useLocation();
  const query = useSearch();
  const enhancedNavigate: typeof navigate = useCallback(
    (to, options) => navigate(urlWithOrgPublicId(to, query), options),
    [navigate, query],
  );

  return [location, enhancedNavigate];
}
