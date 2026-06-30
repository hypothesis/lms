import { IconButton, InfoIcon, Popover } from '@hypothesis/frontend-shared';
import type { Ref } from 'preact';
import { useId, useRef, useState } from 'preact/hooks';

export type DueDateSelectorProps = {
  /**
   * Currently selected due date as a local `datetime-local` string
   * (`YYYY-MM-DDTHH:MM`), or null. The parent converts this to UTC before
   * sending it to the backend.
   */
  dueDate: string | null;
  onChange: (dueDate: string | null) => void;

  /**
   * Earliest selectable value as a `datetime-local` string
   * (`YYYY-MM-DDTHH:MM`). Used to enforce that the due date, when set, is in
   * the future.
   */
  min?: string;

  /** Ref to the underlying input, used by the parent to validate it. */
  inputRef?: Ref<HTMLInputElement>;
};

/**
 * Third step of the "Hide & Reveal" workflow: lets instructors pick the due
 * date, the point at which annotations are no longer tallied in auto grading.
 */
export default function DueDateSelector({
  dueDate,
  onChange,
  min,
  inputRef,
}: DueDateSelectorProps) {
  const headingId = useId();

  // Explanation of the due date, shown in a tooltip (anchored to the info icon)
  // rather than inline. Mirrors the "Max points" popover in FilePickerApp.
  const infoIconRef = useRef<HTMLButtonElement | null>(null);
  const [infoPopoverOpen, setInfoPopoverOpen] = useState(false);

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-x-1">
        <h3 id={headingId} className="uppercase font-medium text-slate-600">
          Due Date
        </h3>
        <IconButton
          icon={InfoIcon}
          title="About due date"
          onClick={() => setInfoPopoverOpen(open => !open)}
          expanded={infoPopoverOpen}
          elementRef={infoIconRef}
          classes="text-[16px]"
        />
        <Popover
          open={infoPopoverOpen}
          anchorElementRef={infoIconRef}
          onClose={() => setInfoPopoverOpen(false)}
          classes="p-2"
          placement="above"
          arrow
        >
          The point where annotations are no longer tallied in auto grading.
          Optional — if set, it must be a future date and time.
        </Popover>
      </div>
      <input
        type="datetime-local"
        data-testid="due-date-input"
        ref={inputRef}
        min={min}
        aria-labelledby={headingId}
        // The shared `Input` component does not support `type="datetime-local"`,
        // so this mirrors its base classes (`inputStyles`) to stay visually
        // consistent, including `touch:text-at-least-16px` which prevents iOS
        // zoom-on-focus.
        className="focus-visible:ring focus-visible:outline-none ring-inset border rounded w-full p-2 bg-grey-0 focus:bg-white disabled:bg-grey-1 placeholder:text-grey-6 disabled:placeholder:text-grey-7 touch:text-at-least-16px"
        value={dueDate ?? ''}
        onChange={e => {
          const { value } = e.target as HTMLInputElement;
          onChange(value === '' ? null : value);
        }}
      />
    </div>
  );
}
