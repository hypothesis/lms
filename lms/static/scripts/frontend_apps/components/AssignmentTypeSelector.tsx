import { RadioGroup } from '@hypothesis/frontend-shared';

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

export type AssignmentTypeSelectorProps = {
  /**
   * Assignment types the instructor can choose from, in display order. Decided
   * by the backend. A new type also needs an entry in the `AssignmentType`
   * union and in `ASSIGNMENT_TYPE_LABELS` to render with a proper label.
   */
  types: AssignmentType[];
  selected: AssignmentType;
  onChange: (type: AssignmentType) => void;
};

/**
 * First step of the assignment-type workflow: lets instructors choose which
 * kind of assignment they are creating among the available `types`.
 */
export default function AssignmentTypeSelector({
  types,
  selected,
  onChange,
}: AssignmentTypeSelectorProps) {
  return (
    <div>
      <RadioGroup
        data-testid="assignment-type-radio-group"
        aria-label="Assignment mode"
        direction="vertical"
        selected={selected}
        onChange={onChange}
      >
        {types.map(type => {
          // Fall back to the raw key if the backend sends a type this frontend
          // build doesn't know yet (deploy ordering), so the radio is never
          // blank. Statically unreachable, but `type` is backend JSON at runtime.
          // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
          const label = ASSIGNMENT_TYPE_LABELS[type] ?? type;
          return (
            <RadioGroup.Radio key={type} value={type}>
              {label}
            </RadioGroup.Radio>
          );
        })}
      </RadioGroup>
    </div>
  );
}
