import type { PanelProps } from '@hypothesis/frontend-shared';
import { Button, Callout, Checkbox, Panel } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useCallback } from 'preact/hooks';

import type { EmailPreferences as SelectedDays, WeekDay } from '../config';

const dayNames: [WeekDay, string][] = [
  ['sun', 'Sunday'],
  ['mon', 'Monday'],
  ['tue', 'Tuesday'],
  ['wed', 'Wednesday'],
  ['thu', 'Thursday'],
  ['fri', 'Friday'],
  ['sat', 'Saturday'],
];

export type EmailPreferencesProps = {
  /** Currently selected days */
  selectedDays: SelectedDays;
  /** Callback to fully or partially update currently selected days, without saving */
  updateSelectedDays: (newSelectedDays: Partial<SelectedDays>) => void;

  /** Callback invoked when saving currently selected days */
  onSave: (submitEvent: Event) => void;
  /** Indicates if a save operation is in progress */
  saving?: boolean;
  /**
   * Represents the result of saving preferences, which can be error or success,
   * and includes a message to display.
   */
  result?: {
    status: 'success' | 'error';
    message: string;
  };

  /**
   * Callback used to handle closing the panel.
   * If not provided, then the panel won't be considered closable.
   */
  onClose?: PanelProps['onClose'];
};

export default function EmailPreferences({
  selectedDays,
  updateSelectedDays,
  onSave,
  saving = false,
  result,
  onClose,
}: EmailPreferencesProps) {
  const setAllTo = useCallback(
    (enabled: boolean) =>
      updateSelectedDays({
        sun: enabled,
        mon: enabled,
        tue: enabled,
        wed: enabled,
        thu: enabled,
        fri: enabled,
        sat: enabled,
      }),
    [updateSelectedDays]
  );
  const selectAll = useCallback(() => setAllTo(true), [setAllTo]);
  const selectNone = useCallback(() => setAllTo(false), [setAllTo]);

  return (
    <form onSubmit={onSave} method="post">
      <Panel
        onClose={onClose}
        title="Email Notifications"
        buttons={
          <Button
            variant="primary"
            type="submit"
            disabled={saving}
            data-testid="save-button"
          >
            Save
          </Button>
        }
      >
        <p className="font-bold">
          Receive email notifications when your students annotate.
        </p>
        <p className="font-bold">Select the days you{"'"}d like your emails:</p>

        <div className="flex justify-between px-4">
          <div className="flex flex-col gap-1">
            {dayNames.map(([day, name]) => (
              <span
                key={day}
                className={classnames(
                  // The checked icon sets fill from the text color
                  'text-grey-6'
                )}
              >
                <Checkbox
                  name={day}
                  checked={selectedDays[day]}
                  onChange={() =>
                    updateSelectedDays({ [day]: !selectedDays[day] })
                  }
                  data-testid={`${day}-checkbox`}
                >
                  <span
                    className={classnames(
                      // Override the color set for the checkbox fill
                      'text-grey-9'
                    )}
                  >
                    {name}
                  </span>
                </Checkbox>
              </span>
            ))}
          </div>
          <div className="flex items-start gap-2">
            <Button
              variant="secondary"
              type="button"
              onClick={selectAll}
              data-testid="select-all-button"
            >
              Select all
            </Button>
            <Button
              variant="secondary"
              type="button"
              onClick={selectNone}
              data-testid="select-none-button"
            >
              Select none
            </Button>
          </div>
        </div>
        {result && <Callout status={result.status}>{result.message}</Callout>}
      </Panel>
    </form>
  );
}
