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

  const [location, navigate] = useLocation();
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
