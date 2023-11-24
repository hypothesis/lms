import { useState } from 'preact/hooks';

import { useConfig } from '../config';
import EmailNotificationsPreferences from './EmailNotificationsPreferences';

export default function EmailPreferencesApp() {
  const { emailNotifications } = useConfig(['emailNotifications']);
  const [selectedDays, setSelectedDays] = useState(emailNotifications);

  return (
    <div className="h-full grid place-items-center">
      <div className="w-96">
        <EmailNotificationsPreferences
          selectedDays={selectedDays}
          setSelectedDays={setSelectedDays}
        />
      </div>
    </div>
  );
}
