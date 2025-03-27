import { Button, Checkbox } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useCallback } from 'preact/hooks';

import type { SelectedDays, WeekDay } from '../config';

const dayNames: [WeekDay, string][] = [
  ['sun', 'Sunday'],
  ['mon', 'Monday'],
  ['tue', 'Tuesday'],
  ['wed', 'Wednesday'],
  ['thu', 'Thursday'],
  ['fri', 'Friday'],
  ['sat', 'Saturday'],
];

export type EmailDigestPreferencesProps = {
  /** Currently selected days */
  selectedDays: SelectedDays;
  /** Callback to fully or partially update currently selected days, without saving */
  onSelectedDaysChange: (newSelectedDays: Partial<SelectedDays>) => void;
};

export default function EmailDigestPreferences({
  selectedDays,
  onSelectedDaysChange,
}: EmailDigestPreferencesProps) {
  const setAllTo = useCallback(
    (enabled: boolean) =>
      onSelectedDaysChange({
        sun: enabled,
        mon: enabled,
        tue: enabled,
        wed: enabled,
        thu: enabled,
        fri: enabled,
        sat: enabled,
      }),
    [onSelectedDaysChange],
  );
  const selectAll = useCallback(() => setAllTo(true), [setAllTo]);
  const selectNone = useCallback(() => setAllTo(false), [setAllTo]);

  return (
    <div className="flex flex-col gap-y-3">
      <h2 className="text-lg/6 text-brand">Student activity digest</h2>
      <p>Receive email notifications when your students annotate.</p>
      <p>Select the days you{"'"}d like your emails:</p>

      <div className="flex justify-between pl-4">
        <div className="flex flex-col gap-1">
          {dayNames.map(([day, name]) => (
            <span
              key={day}
              className={classnames(
                // The checked icon sets fill from the text color
                'text-grey-6',
              )}
            >
              <Checkbox
                name={day}
                checked={selectedDays[day]}
                onChange={() =>
                  onSelectedDaysChange({ [day]: !selectedDays[day] })
                }
                data-testid={`${day}-checkbox`}
              >
                <span
                  className={classnames(
                    // Override the color set for the checkbox fill
                    'text-grey-9',
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
    </div>
  );
}
