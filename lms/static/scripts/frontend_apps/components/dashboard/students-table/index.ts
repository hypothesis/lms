import { useCallback, useMemo } from 'preact/hooks';

import type { AssignmentDetails } from '../../../api-types';
import { autoGradingVariant } from './auto-grading';
import { checkpointAutoGradingVariant, checkpointVariant } from './checkpoint';
import { plainVariant } from './plain';
import type {
  AnyStudentsTableRow,
  AssignmentCapability,
  ConditionalVariantModule,
  GradeToSync,
  RenderContext,
  StudentsTableConfig,
  StudentsTableVariantModule,
  VariantContext,
} from './types';

/**
 * How each capability is detected on an assignment.
 *
 * This is the only place which reads the fields behind them, so a variant never
 * has to know about a capability it does not handle. Detecting them from the
 * data the API returns rather than from explicit flags is what lets an
 * assignment fall through to a more basic variant instead of breaking.
 */
const CAPABILITY_DETECTORS: Record<
  AssignmentCapability,
  (assignment?: AssignmentDetails | null) => boolean
> = {
  'auto-grading': assignment => !!assignment?.auto_grading_config,
  checkpoints: assignment => !!assignment?.checkpoint_enabled,
};

/**
 * Capabilities this assignment exposes, as far as this version of the frontend
 * knows: one it does not know about is not detected at all, which is what makes
 * such an assignment fall back to a more basic variant.
 */
function capabilitiesOf(
  assignment?: AssignmentDetails | null,
): Set<AssignmentCapability> {
  const detected = new Set<AssignmentCapability>();

  for (const capability of Object.keys(
    CAPABILITY_DETECTORS,
  ) as AssignmentCapability[]) {
    if (CAPABILITY_DETECTORS[capability](assignment)) {
      detected.add(capability);
    }
  }

  return detected;
}

/**
 * Variants which only handle an assignment exposing a given capability.
 *
 * `plainVariant` handles the assignments with no capability at all, and is the
 * fallback for a combination no variant declares.
 *
 * The order of this list is irrelevant: a variant owns the assignments whose
 * capabilities are exactly the ones it declares, so at most one of these can
 * claim any given assignment.
 */
export const VARIANT_MODULES: ConditionalVariantModule<AnyStudentsTableRow>[] =
  [autoGradingVariant, checkpointVariant, checkpointAutoGradingVariant];

/** Resolve the variant which handles this assignment. */
export function resolveVariantModule(
  assignment?: AssignmentDetails | null,
): StudentsTableVariantModule<AnyStudentsTableRow> {
  const capabilities = capabilitiesOf(assignment);

  return (
    VARIANT_MODULES.find(
      ({ handles }) =>
        handles.length === capabilities.size &&
        handles.every(capability => capabilities.has(capability)),
    ) ?? plainVariant
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

export type StudentsTableConfigOptions = RenderContext;

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
}: StudentsTableConfigOptions): StudentsTableConfig<AnyStudentsTableRow> {
  // Variant modules are singletons, so this is stable across renders as long as
  // the assignment keeps resolving to the same variant.
  const variantModule = resolveVariantModule(assignment);

  const rows = useMemo(
    () => variantModule.buildRows(students ?? []),
    [students, variantModule],
  );
  const columns = useMemo(
    () => variantModule.columns({ assignment, students }),
    [assignment, students, variantModule],
  );
  const renderItem = useCallback(
    (row: AnyStudentsTableRow, field: keyof AnyStudentsTableRow) =>
      variantModule.renderItem(row, field, {
        assignment,
        students,
        studentSyncStatuses,
      }),
    [assignment, students, studentSyncStatuses, variantModule],
  );

  return { rows, columns, renderItem };
}

export type StudentsToSyncOptions = VariantContext;

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
