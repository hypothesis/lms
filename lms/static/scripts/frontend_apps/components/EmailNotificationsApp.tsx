import { useState } from 'preact/hooks';

import { useConfig } from '../config';
import EmailNotificationsPreferences from './EmailNotificationsPreferences';

export default function EmailNotificationsApp() {
  const { emailNotifications } = useConfig(['emailNotifications']);
  const [selectedDays, setSelectedDays] = useState(emailNotifications);

  return (
    <div className="h-full grid place-items-center">
      <div className="w-96">
        <EmailNotificationsPreferences
          selectedDays={selectedDays}
          updateSelectedDays={newSelectedDays =>
            setSelectedDays(prev => ({ ...prev, ...newSelectedDays }))
          }
        />
      </div>
    </div>
  );
}
