import { useCallback, useMemo } from 'preact/hooks';
import { useLocation, useSearch } from 'wouter-preact';

import { queryStringToRecord, recordToQueryString } from '../url';

export type DashboardFilters = {
  studentIds: string[];
  assignmentIds: string[];
  courseIds: string[];
};

export type URLWithFiltersOptions = {
  /** The path to navigate to. Defaults to current path */
  path?: string;

  /**
   * Whether provided filters should extend existing ones.
   * Defaults to false.
   */
  extend?: boolean;
};

export type UseDashboardFilters = {
  /** Current filters */
  filters: DashboardFilters;
  /** Navigate to current URL with provided filters */
  updateFilters: (filtersToUpdate: Partial<DashboardFilters>) => void;
  /** Generate a URL with provided filters */
  urlWithFilters: (
    filtersToUpdate: Partial<DashboardFilters>,
    options?: URLWithFiltersOptions,
  ) => string;
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
  const urlWithFilters = useCallback(
    (
      { courseIds, assignmentIds, studentIds }: Partial<DashboardFilters>,
      { path = location, extend = false }: URLWithFiltersOptions = {},
    ): string => {
      const newQueryParams = extend ? { ...queryParams } : {};
      if (courseIds) {
        newQueryParams.course_id = courseIds;
      }
      if (assignmentIds) {
        newQueryParams.assignment_id = assignmentIds;
      }
      if (studentIds) {
        newQueryParams.student_id = studentIds;
      }

      return `${path}${recordToQueryString(newQueryParams)}`;
    },
    [location, queryParams],
  );

  const updateFilters = useCallback(
    (filters: Partial<DashboardFilters>) =>
      navigate(urlWithFilters(filters, { extend: true }), { replace: true }),
    [navigate, urlWithFilters],
  );

  return { filters, updateFilters, urlWithFilters };
}
