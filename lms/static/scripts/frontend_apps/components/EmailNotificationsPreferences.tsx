import type { PanelProps } from '@hypothesis/frontend-shared';
import { Button, Checkbox, Panel } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useCallback } from 'preact/hooks';

import type { EmailNotificationsPreferences, WeekDay } from '../config';

const dayNames: [WeekDay, string][] = [
  ['sun', 'Sunday'],
  ['mon', 'Monday'],
  ['tue', 'Tuesday'],
  ['wed', 'Wednesday'],
  ['thu', 'Thursday'],
  ['fri', 'Friday'],
  ['sat', 'Saturday'],
];

export type EmailNotificationsPreferencesProps = {
  selectedDays: EmailNotificationsPreferences;
  updateSelectedDays: (
    newSelectedDays: Partial<EmailNotificationsPreferences>
  ) => void;
  onClose?: PanelProps['onClose'];
};

export default function EmailNotificationsPreferences({
  onClose,
  selectedDays,
  updateSelectedDays,
}: EmailNotificationsPreferencesProps) {
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
    <Panel
      onClose={onClose}
      title="Email Notifications"
      buttons={<Button variant="primary">Save</Button>}
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
            onClick={selectAll}
            data-testid="select-all-button"
          >
            Select all
          </Button>
          <Button
            variant="secondary"
            onClick={selectNone}
            data-testid="select-none-button"
          >
            Select none
          </Button>
        </div>
      </div>
    </Panel>
  );
}
