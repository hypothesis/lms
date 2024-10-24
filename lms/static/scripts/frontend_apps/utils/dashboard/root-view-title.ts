import type { DashboardConfig } from '../../config';

/**
 * Return the title for the dashboard's root view.
 *
 * That is the organization name if the dashboard was launched for one specific
 * org, or 'All courses' otherwise.
 */
export function rootViewTitle(dashboardConfig: DashboardConfig): string {
  return dashboardConfig.organization?.name ?? 'All courses';
}
