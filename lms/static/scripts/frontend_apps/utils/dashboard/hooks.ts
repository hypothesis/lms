import { useCallback, useMemo } from 'preact/hooks';
import { useLocation, useSearch } from 'wouter-preact';

import { queryStringToRecord, recordToQueryString } from '../url';

export type DashboardFilters = {
  studentIds: string[];
  assignmentIds: string[];
  courseIds: string[];

  /**
   * The list of segments (groups or sections) to filter students by.
   * This filter is relevant only when listing students in the assignment view.
   */
  segmentIds: string[];
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

function asArray(value: string | string[] = []): string[] {
  return Array.isArray(value) ? value : [value];
}

/**
 * Hook used to read and update the state of the dashboard filters.
 *
 * The filter state is synchronized with query string parameters in the URL.
 */
export function useDashboardFilters(): UseDashboardFilters {
  const search = useSearch();
  const queryParams = useMemo(() => queryStringToRecord(search), [search]);
  const filters = useMemo(() => {
    const courseIds = asArray(queryParams.course_id);
    const assignmentIds = asArray(queryParams.assignment_id);
    const studentIds = asArray(queryParams.student_id);
    const segmentIds = asArray(queryParams.segment_id);

    return { courseIds, assignmentIds, studentIds, segmentIds };
  }, [queryParams]);

  const [location, navigate] = useLocation();
  const urlWithFilters = useCallback(
    (
      {
        courseIds,
        assignmentIds,
        studentIds,
        segmentIds,
      }: Partial<DashboardFilters>,
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
      if (segmentIds) {
        newQueryParams.segment_id = segmentIds;
      }

      // The router's base URL is represented in `location` as '/', even if
      // that URL does not actually end with `/` (eg. `/dashboard`).
      // When we update the query string, we want to avoid modifying the path
      // unless a path was explicitly provided.
      const normalizedPath = path === '/' ? '' : path;

      return `${normalizedPath}${recordToQueryString(newQueryParams)}`;
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
