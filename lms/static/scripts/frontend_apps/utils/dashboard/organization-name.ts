import type { DashboardConfig } from '../../config';

export function organizationName(dashboardConfig: DashboardConfig): string {
  return dashboardConfig.organization?.name ?? 'All courses';
}
