import Library from '@hypothesis/frontend-shared/lib/pattern-library/components/Library';
import { useState } from 'preact/hooks';

import DueDateSelector from '../../frontend_apps/components/DueDateSelector';

/** Local `datetime-local` string (`YYYY-MM-DDTHH:MM`) for `date`. */
function localDateTime(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}`
  );
}

/**
 * Wraps the selector with the state the real parent (`FilePickerApp`) holds,
 * and shows the value it reports back.
 */
function Demo({ initial = null }: { initial?: string | null }) {
  const [dueDate, setDueDate] = useState<string | null>(initial);
  const min = localDateTime(new Date());

  return (
    <div className="space-y-3">
      <DueDateSelector dueDate={dueDate} onChange={setDueDate} min={min} />
      <div className="text-sm space-y-1">
        <p>
          Reported to the parent:{' '}
          <code>{dueDate === null ? 'null' : dueDate}</code>
        </p>
        <p>
          Submitted to the backend:{' '}
          <code>
            {dueDate === null ? 'null' : new Date(dueDate).toISOString()}
          </code>
        </p>
        <p className="text-grey-6">
          Earliest selectable value (<code>min</code>): <code>{min}</code>
        </p>
      </div>
    </div>
  );
}

export default function DueDateSelectorPage() {
  return (
    <Library.Page title="Due date selector">
      <Library.Section title="DueDateSelector">
        <p>
          Third step of the &ldquo;Paced Social Annotation&rdquo; (Hide &amp;
          Reveal) assignment-creation workflow. The date and time are picked in
          separate fields, as in Canvas, but the component reports a single
          combined <code>YYYY-MM-DDTHH:MM</code> value &mdash; the backend still
          stores one <code>datetime</code>.
        </p>
        <Library.Demo withSource>
          <Demo />
        </Library.Demo>
      </Library.Section>

      <Library.Section title="With an existing due date">
        <p>
          When editing an assignment that already has a due date, the stored
          value is split back across the two fields.
        </p>
        <Library.Demo withSource>
          <Demo initial="2030-06-11T14:30" />
        </Library.Demo>
      </Library.Section>

      <Library.Section title="Things to try">
        <p>
          The fields are only meaningful as a pair, so each one is{' '}
          <code>required</code> once the other is filled in. The value reported
          above stays <code>null</code> until both are set, and the browser
          blocks the step with a native warning:
        </p>
        <ul>
          <li>
            Pick a date and leave the time empty &mdash; the time is{' '}
            <em>not</em> defaulted, and the reported value stays{' '}
            <code>null</code>.
          </li>
          <li>Enter a time before picking a date &mdash; same, in reverse.</li>
          <li>
            Clear the date &mdash; the time is cleared with it, rather than
            lingering on its own.
          </li>
          <li>
            Pick today&apos;s date, then a time earlier than now &mdash;
            rejected by the time field&apos;s <code>min</code>. On any later
            date, every time of day is accepted.
          </li>
        </ul>
      </Library.Section>
    </Library.Page>
  );
}
