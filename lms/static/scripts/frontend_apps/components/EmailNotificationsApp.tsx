import { useCallback, useState } from 'preact/hooks';

import { useConfig } from '../config';
import EmailNotificationsPreferences from './EmailNotificationsPreferences';

export default function EmailNotificationsApp() {
  const { emailNotifications } = useConfig(['emailNotifications']);
  const [selectedDays, setSelectedDays] = useState(emailNotifications);
  const [saving, setSaving] = useState(false);
  const onSave = useCallback(() => setSaving(true), []);

  return (
    <div className="h-full grid place-items-center">
      <div className="w-96">
        <EmailNotificationsPreferences
          selectedDays={selectedDays}
          updateSelectedDays={newSelectedDays =>
            setSelectedDays(prev => ({ ...prev, ...newSelectedDays }))
          }
          onSave={onSave}
          saving={saving}
        />
      </div>
    </div>
  );
}
