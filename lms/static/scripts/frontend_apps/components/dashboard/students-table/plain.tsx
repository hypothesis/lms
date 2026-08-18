import {
  buildRows,
  metricsColumns,
  renderSharedField,
  studentColumn,
} from './shared';
import type { StudentsTableVariantModule } from './types';

/**
 * Annotation metrics only: the table of an assignment without any grading
 * capability.
 *
 * This is the fallback of the registry: it handles every assignment no other
 * variant claims, so it has nothing to match on.
 */
export const plainVariant: StudentsTableVariantModule = {
  variant: 'plain',
  buildRows,
  columns: () => [studentColumn, ...metricsColumns],
  renderItem: renderSharedField,
};
