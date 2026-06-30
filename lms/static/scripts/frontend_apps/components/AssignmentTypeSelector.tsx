import { OptionButton } from '@hypothesis/frontend-shared';

/**
 * The kind of assignment being created.
 *
 * - `reading`: a standard "Social annotation" reading assignment.
 * - `hide_and_reveal`: "Guided Social annotation" — students' annotations are
 *   hidden from each other until an instructor reveals them (internally also
 *   referred to as "Hide & Reveal" / checkpoints).
 */
export type AssignmentType = 'reading' | 'hide_and_reveal';

/** Human-readable label shown in the selector for each assignment type. */
const ASSIGNMENT_TYPE_LABELS: Record<AssignmentType, string> = {
  reading: 'Social annotation',
  hide_and_reveal: 'Guided Social annotation',
};

/** Short description shown under each option's label. */
const ASSIGNMENT_TYPE_DETAILS: Record<AssignmentType, string> = {
  reading: 'Standard annotation',
  hide_and_reveal: 'Hidden until revealed',
};

export type AssignmentTypeSelectorProps = {
  /**
   * Assignment types the instructor can choose from, in display order. Decided
   * by the backend. A new type also needs an entry in the `AssignmentType`
   * union and in `ASSIGNMENT_TYPE_LABELS` to render with a proper label.
   */
  types: AssignmentType[];

  /**
   * Called when the instructor picks a type. Selecting a type advances the
   * workflow immediately, so this step has no separate "Next" button (it
   * mirrors the content-selection buttons).
   */
  onSelect: (type: AssignmentType) => void;
};

/**
 * First step of the assignment-type workflow: lets instructors choose which
 * kind of assignment they are creating among the available `types`. Rendered as
 * clickable buttons (like the content selector) that advance on click.
 */
export default function AssignmentTypeSelector({
  types,
  onSelect,
}: AssignmentTypeSelectorProps) {
  return (
    <div className="grid grid-cols-1 gap-y-2 w-fit">
      {types.map(type => {
        // Fall back to the raw key if the backend sends a type this frontend
        // build doesn't know yet (deploy ordering), so the button is never
        // blank. Statically unreachable, but `type` is backend JSON at runtime.
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
        const label = ASSIGNMENT_TYPE_LABELS[type] ?? type;
        const details = ASSIGNMENT_TYPE_DETAILS[type];
        return (
          <OptionButton
            key={type}
            data-testid={`assignment-type-${type}`}
            // Extra left margin adds a bit of breathing room between the label
            // and the right-aligned description.
            details={details && <span className="ml-4">{details}</span>}
            onClick={() => onSelect(type)}
          >
            {label}
          </OptionButton>
        );
      })}
    </div>
  );
}
