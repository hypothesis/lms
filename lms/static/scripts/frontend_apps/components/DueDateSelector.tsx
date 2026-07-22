import { IconButton, InfoIcon, Popover } from '@hypothesis/frontend-shared';
import type { Ref } from 'preact';
import { useId, useRef, useState } from 'preact/hooks';

const TIME_STEP_MINUTES = 30;
const MINUTES_PER_DAY = 24 * 60;

const pad = (n: number) => String(n).padStart(2, '0');

function splitDateTime(value: string | null): [string, string] {
  if (!value) {
    return ['', ''];
  }
  const [date = '', time = ''] = value.split('T');
  return [date, time];
}

/** Format a 24-hour `HH:MM` time for display, e.g. `13:30` -> `1:30 PM`. */
function formatTime(time: string): string {
  const [hours, minutes] = time.split(':').map(Number);
  const period = hours < 12 ? 'AM' : 'PM';
  // Midnight (0) and noon (12) both display as 12.
  const hour12 = hours % 12 || 12;
  return `${hour12}:${pad(minutes)} ${period}`;
}

/**
 * The `HH:MM` times offered in the dropdown, every `TIME_STEP_MINUTES`.
 *
 * `include` adds a time that isn't on that grid. A due date saved before this
 * dropdown existed can hold any minute, and dropping it from the options would
 * silently change the assignment's due date.
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

  /** Earliest selectable value, as a `YYYY-MM-DDTHH:MM` string. */
  min?: string;

  /** Ref to the date input, used by the parent to validate it. */
  inputRef?: Ref<HTMLInputElement>;

  /**
   * Ref to the time dropdown. Each field carries its own constraints, so the
   * parent checks both.
   */
  timeInputRef?: Ref<HTMLSelectElement>;
};

/**
 * Third step of the "Hide & Reveal" workflow: lets instructors pick the due
 * date, the point at which annotations are no longer tallied in auto grading.
 *
 * The date and time are picked in separate fields (as in Canvas), but the
 * component reports a single combined `YYYY-MM-DDTHH:MM` value, so the parent
 * keeps working with one string.
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

  // The fields can be filled in either order, and the parent only stores the
  // combined value (null until both halves exist), so the half-entered state
  // has to live here or a lone time would vanish on re-render.
  const [dateValue, setDateValue] = useState(() => splitDateTime(dueDate)[0]);
  const [timeValue, setTimeValue] = useState(() => splitDateTime(dueDate)[1]);

  const [minDate, minTime] = splitDateTime(min ?? null);

  // Explanation of the due date, shown in a tooltip (anchored to the info icon)
  // rather than inline. Mirrors the "Max points" popover in FilePickerApp.
  const infoIconRef = useRef<HTMLButtonElement | null>(null);
  const [infoPopoverOpen, setInfoPopoverOpen] = useState(false);

  const emit = (date: string, time: string) =>
    onChange(date && time ? `${date}T${time}` : null);

  const onDateChange = (date: string) => {
    // Clearing the date unsets the due date as a whole, so the time goes with
    // it rather than lingering on its own.
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
  // does not support `type="date"` or `select`. `touch:text-at-least-16px`
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
      <div
        role="group"
        aria-labelledby={headingId}
        className="flex flex-col sm:flex-row sm:items-center gap-2 sm:gap-x-4"
      >
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
            // Each field is required once the other is filled, so a
            // half-entered due date fails validation instead of being read as
            // the legal "left blank".
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
                // Only the earliest selectable date can hold past times; on any
                // later date every time of day is still in the future.
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
