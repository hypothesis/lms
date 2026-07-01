import { RadioGroup } from '@hypothesis/frontend-shared';
import { useId } from 'preact/hooks';

/**
 * The kind of checkpoint that controls when hidden annotations are revealed.
 *
 * For now only `manual` is functional (the instructor reveals annotations
 * themselves); more options (e.g. a calendar/date-driven checkpoint) are
 * planned.
 */
export type CheckpointType = 'manual';

/** Values rendered as radios, including not-yet-available options. */
type CheckpointOption = CheckpointType | 'more';

export type CheckpointSelectorProps = {
  selected: CheckpointType;
  onChange: (type: CheckpointType) => void;
};

/**
 * Second step of the "Hide & Reveal" workflow: lets instructors choose how the
 * checkpoint (the point at which hidden annotations are revealed) works.
 */
export default function CheckpointSelector({
  selected,
  onChange,
}: CheckpointSelectorProps) {
  const headingId = useId();

  // The note below is specific to the "manual" reveal, so it only shows for that
  // option. `selected` is currently always 'manual' (the only enabled option),
  // but this keeps the association explicit for when more types are added.
  // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
  const showManualNote = selected === 'manual';

  return (
    <div className="space-y-2">
      <h3 id={headingId} className="uppercase font-medium text-slate-600">
        Checkpoint
      </h3>
      <RadioGroup<CheckpointOption>
        data-testid="checkpoint-radio-group"
        aria-labelledby={headingId}
        direction="vertical"
        selected={selected}
        onChange={option => {
          // Ignore the disabled "coming soon" placeholder; anything else is a
          // real CheckpointType. Adding a new type needs no change here.
          if (option !== 'more') {
            onChange(option);
          }
        }}
      >
        <RadioGroup.Radio value="manual">Manual</RadioGroup.Radio>
        <RadioGroup.Radio value="more" disabled>
          More coming soon
        </RadioGroup.Radio>
      </RadioGroup>
      {showManualNote && (
        // No color class: inherits the base text color (black) per design.
        <p>
          Students will see when the settings have changed from
          &ldquo;Hide&rdquo; to &ldquo;Reveal&rdquo; in their notifications.
        </p>
      )}
    </div>
  );
}
