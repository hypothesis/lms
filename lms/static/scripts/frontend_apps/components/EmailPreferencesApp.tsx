import { useCallback, useState } from 'preact/hooks';

import { useConfig } from '../config';
import EmailPreferences from './EmailPreferences';

export default function EmailPreferencesApp() {
  const { emailPreferences } = useConfig(['emailPreferences']);
  const [selectedDays, setSelectedDays] = useState(emailPreferences);
  const [saving, setSaving] = useState(false);
  const onSave = useCallback(() => setSaving(true), []);

  return (
    <div className="h-full grid place-items-center">
      <div className="w-96">
        <EmailPreferences
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
