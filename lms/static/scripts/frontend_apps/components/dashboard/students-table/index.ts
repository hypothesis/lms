import { useCallback, useMemo } from 'preact/hooks';

import type {
  AssignmentDetails,
  StudentGradingSyncStatus,
  StudentWithMetrics,
} from '../../../api-types';
import { autoGradingVariant } from './auto-grading';
import { plainVariant } from './plain';
import type {
  ConditionalVariantModule,
  GradeToSync,
  StudentsTableConfig,
  StudentsTableRow,
  StudentsTableVariantModule,
} from './types';

/**
 * Variants which only handle an assignment exposing a given capability. The
 * first one which matches the assignment owns the table.
 *
 * `plainVariant` handles everything none of these claim, so an assignment with
 * a capability this version of the frontend does not know about still renders
 * its annotation metrics instead of breaking.
 *
 * Order matters, and nothing enforces that the `matches` predicates are
 * mutually exclusive: an assignment matching two of them silently gets the one
 * listed first, including its `gradesToSync`, which would grade students by the
 * wrong rule without surfacing an error. Keep this ordered from the most
 * specific capability to the least, so that a variant which handles a narrower
 * case than another is listed before it.
 */
const VARIANT_MODULES: ConditionalVariantModule[] = [autoGradingVariant];

/** Resolve the variant which handles this assignment. */
export function resolveVariantModule(
  assignment?: AssignmentDetails | null,
): StudentsTableVariantModule {
  return (
    VARIANT_MODULES.find(module => module.matches(assignment)) ?? plainVariant
  );
}

/**
 * Whether grades of this assignment can be synced to the LMS.
 *
 * This gates the sync button and the polling of the last sync status, so a
 * variant which does not grade never issues those requests.
 */
export function assignmentSyncsGrades(
  assignment?: AssignmentDetails | null,
): boolean {
  return !!resolveVariantModule(assignment).gradesToSync;
}

export type StudentsTableConfigOptions = {
  students?: StudentWithMetrics[];
  assignment?: AssignmentDetails | null;
  /** Status of the most recent grade sync, per student. */
  studentSyncStatuses: Record<string, StudentGradingSyncStatus>;
};

/**
 * Build the rows, columns and item renderer of the students table.
 *
 * These three vary together for a given variant, so they are resolved from one
 * module instead of being derived separately by the view.
 */
export function useStudentsTableConfig({
  students,
  assignment,
  studentSyncStatuses,
}: StudentsTableConfigOptions): StudentsTableConfig {
  // Variant modules are singletons, so this is stable across renders as long as
  // the assignment keeps resolving to the same variant.
  const variantModule = resolveVariantModule(assignment);

  const rows = useMemo(
    () => variantModule.buildRows(students ?? []),
    [students, variantModule],
  );
  const columns = useMemo(() => variantModule.columns(), [variantModule]);
  const renderItem = useCallback(
    (row: StudentsTableRow, field: keyof StudentsTableRow) =>
      variantModule.renderItem(row, field, {
        assignment,
        studentSyncStatuses,
      }),
    [assignment, studentSyncStatuses, variantModule],
  );

  return { rows, columns, renderItem };
}

export type StudentsToSyncOptions = {
  students?: StudentWithMetrics[];
  assignment?: AssignmentDetails | null;
};

/**
 * Grades to send to the LMS on the next sync, for the variant of this
 * assignment.
 *
 * An empty array means every grade is already synced. `undefined` means the
 * list is not known instead: either the students are still loading, or this
 * variant does not grade at all. `SyncGradesButton` renders as loading in both
 * of those cases, and it is only displayed for variants which grade.
 */
export function useStudentsToSync({
  students,
  assignment,
}: StudentsToSyncOptions): GradeToSync[] | undefined {
  const variantModule = resolveVariantModule(assignment);

  return useMemo(
    () => (students ? variantModule.gradesToSync?.(students) : undefined),
    [students, variantModule],
  );
}
