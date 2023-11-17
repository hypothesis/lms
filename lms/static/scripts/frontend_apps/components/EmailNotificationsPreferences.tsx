import type { PanelProps } from '@hypothesis/frontend-shared';
import { Button, Checkbox, Panel } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { StateUpdater } from 'preact/hooks';
import { useCallback } from 'preact/hooks';

import type { EmailNotificationsPreferences, WeekDay } from '../config';

const dayNames: [WeekDay, string][] = [
  [7, 'Sunday'],
  [1, 'Monday'],
  [2, 'Tuesday'],
  [3, 'Wednesday'],
  [4, 'Thursday'],
  [5, 'Friday'],
  [6, 'Saturday'],
];

export type EmailNotificationsPreferencesProps = {
  selectedDays: EmailNotificationsPreferences;
  setSelectedDays: StateUpdater<EmailNotificationsPreferences>;
  onClose?: PanelProps['onClose'];
};

export default function EmailNotificationsPreferences({
  onClose,
  selectedDays,
  setSelectedDays,
}: EmailNotificationsPreferencesProps) {
  const setAllTo = useCallback(
    (enabled: boolean) =>
      setSelectedDays({
        1: enabled,
        2: enabled,
        3: enabled,
        4: enabled,
        5: enabled,
        6: enabled,
        7: enabled,
      }),
    [setSelectedDays]
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
                  setSelectedDays(prev => ({ ...prev, [day]: !prev[day] }))
                }
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
          <Button variant="secondary" onClick={selectAll}>
            Select All
          </Button>
          <Button variant="secondary" onClick={selectNone}>
            Select None
          </Button>
        </div>
      </div>
    </Panel>
  );
}
