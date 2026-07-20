import { IconButton, InfoIcon, Popover } from '@hypothesis/frontend-shared';
import type { Ref } from 'preact';
import { useId, useRef, useState } from 'preact/hooks';

/** Split a `YYYY-MM-DDTHH:MM` string into its date and time halves. */
function splitDateTime(value: string | null): [string, string] {
  if (!value) {
    return ['', ''];
  }
  const [date = '', time = ''] = value.split('T');
  return [date, time];
}

/** Interval between the times offered in the dropdown, in minutes. */
const TIME_STEP_MINUTES = 30;

const MINUTES_PER_DAY = 24 * 60;

const pad = (n: number) => String(n).padStart(2, '0');

/** Format a 24-hour `HH:MM` time for display, e.g. `13:30` -> `1:30 PM`. */
function formatTime(time: string): string {
  const [hours, minutes] = time.split(':').map(Number);
  const period = hours < 12 ? 'AM' : 'PM';
  // Both midnight (0) and noon (12) display as 12.
  const hour12 = hours % 12 || 12;
  return `${hour12}:${pad(minutes)} ${period}`;
}

/**
 * The `HH:MM` times offered in the dropdown, every `TIME_STEP_MINUTES`.
 *
 * `include` adds a time that isn't on that grid, keeping an already-saved due
 * date selectable: assignments created before this dropdown existed (or
 * through another tool) can hold any minute, and dropping it would silently
 * change the assignment's due date.
 */
function timeOptions(include?: string): string[] {
  const times = [];
  for (
    let minutes = 0;
    minutes < MINUTES_PER_DAY;
    minutes += TIME_STEP_MINUTES
  ) {
    times.push(`${pad(Math.floor(minutes / 60))}:${pad(minutes % 60)}`);
  }

  if (include && !times.includes(include)) {
    times.push(include);
    times.sort();
  }

  return times;
}

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

  /** Ref to the date input, used by the parent to validate it. */
  inputRef?: Ref<HTMLInputElement>;

  /**
   * Ref to the time dropdown. The date and time are separately constrained, so
   * the parent has to check both to catch a half-entered or past due date.
   */
  timeInputRef?: Ref<HTMLSelectElement>;
};

/**
 * Third step of the "Hide & Reveal" workflow: lets instructors pick the due
 * date, the point at which annotations are no longer tallied in auto grading.
 *
 * The date and time are picked in separate fields (as in Canvas), but the
 * component still reports a single combined `YYYY-MM-DDTHH:MM` value, so the
 * parent keeps working with one string.
 */
export default function DueDateSelector({
  dueDate,
  onChange,
  min,
  inputRef,
  timeInputRef,
}: DueDateSelectorProps) {
  const headingId = useId();
  const dateLabelId = useId();
  const timeLabelId = useId();

  // The two fields can be filled in either order, so a time may be entered
  // before a date. The parent only stores the *combined* value (null until
  // both halves exist), so the half-entered state has to live here or the
  // typed time would vanish on re-render.
  const [dateValue, setDateValue] = useState(() => splitDateTime(dueDate)[0]);
  const [timeValue, setTimeValue] = useState(() => splitDateTime(dueDate)[1]);

  const [minDate, minTime] = splitDateTime(min ?? null);

  // Explanation of the due date, shown in a tooltip (anchored to the info icon)
  // rather than inline. Mirrors the "Max points" popover in FilePickerApp.
  const infoIconRef = useRef<HTMLButtonElement | null>(null);
  const [infoPopoverOpen, setInfoPopoverOpen] = useState(false);

  // A due date needs both halves. Reporting null while only one is filled
  // keeps the value the parent submits well-formed.
  const emit = (date: string, time: string) =>
    onChange(date && time ? `${date}T${time}` : null);

  const onDateChange = (date: string) => {
    // Clearing the date unsets the due date as a whole, so the time goes with
    // it rather than lingering as an orphaned value.
    const time = date ? timeValue : '';

    setDateValue(date);
    setTimeValue(time);
    emit(date, time);
  };

  const onTimeChange = (time: string) => {
    setTimeValue(time);
    emit(dateValue, time);
  };

  // Mirrors the shared `Input` component's base classes (`inputStyles`), which
  // does not support `type="date"`/`type="time"`. `touch:text-at-least-16px`
  // prevents iOS zoom-on-focus.
  const inputClasses =
    'focus-visible:ring focus-visible:outline-none ring-inset border rounded p-2 bg-grey-0 focus:bg-white disabled:bg-grey-1 placeholder:text-grey-6 disabled:placeholder:text-grey-7 touch:text-at-least-16px';

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
      {/* Stacks on very narrow screens, side by side (as in Canvas) otherwise. */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-x-4">
        <div className="flex items-center gap-x-2">
          <label id={dateLabelId} htmlFor={`${dateLabelId}-input`}>
            Due date
          </label>
          <input
            type="date"
            id={`${dateLabelId}-input`}
            data-testid="due-date-input"
            ref={inputRef}
            min={minDate || undefined}
            // A time on its own is not a due date. Marking the date required
            // in that case lets the parent's `reportValidity()` catch it,
            // rather than silently dropping the time the instructor entered.
            required={!!timeValue}
            className={inputClasses}
            value={dateValue}
            onChange={e => onDateChange((e.target as HTMLInputElement).value)}
          />
        </div>
        <div className="flex items-center gap-x-2">
          <label id={timeLabelId} htmlFor={`${timeLabelId}-input`}>
            Time
          </label>
          <select
            id={`${timeLabelId}-input`}
            data-testid="due-date-time-input"
            ref={timeInputRef}
            // A date with no time is incomplete rather than "no due date", so
            // the instructor is warned instead of the time being guessed for
            // them.
            required={!!dateValue}
            className={inputClasses}
            value={timeValue}
            onChange={e => onTimeChange((e.target as HTMLSelectElement).value)}
          >
            <option value="">Select a time</option>
            {timeOptions(timeValue || undefined).map(time => (
              <option
                key={time}
                value={time}
                // On the earliest selectable date, times before the minimum are
                // in the past. On any later date every time of day is still in
                // the future, so nothing is disabled.
                disabled={dateValue === minDate && time < minTime}
              >
                {formatTime(time)}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}
