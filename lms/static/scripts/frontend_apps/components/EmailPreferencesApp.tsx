import { InfoIcon, Link } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useCallback, useState } from 'preact/hooks';

import { useConfig } from '../config';
import EmailPreferences from './EmailPreferences';

export default function EmailPreferencesApp() {
  const { emailPreferences } = useConfig(['emailPreferences']);
  const [selectedDays, setSelectedDays] = useState(emailPreferences);
  const [saving, setSaving] = useState(false);
  const onSave = useCallback(() => setSaving(true), []);

  return (
    <div className="min-h-full bg-grey-2">
      <div
        className={classnames(
          'flex justify-center p-3 w-full',
          'bg-white border-b shadow'
        )}
      >
        <img
          alt="Hypothesis logo"
          src="/static/images/email_header.png"
          className="h-10"
        />
      </div>
      <div className="flex flex-col gap-y-4 py-8">
        <div className="max-w-[450px] mx-auto">
          <EmailPreferences
            selectedDays={selectedDays}
            updateSelectedDays={newSelectedDays =>
              setSelectedDays(prev => ({ ...prev, ...newSelectedDays }))
            }
            onSave={onSave}
            saving={saving}
          />
        </div>
        <p className="text-center text-grey-8">
          <InfoIcon className="inline" /> Do you need help? Visit our{' '}
          <Link
            variant="custom"
            underline="always"
            href="https://web.hypothes.is/help/"
          >
            help center
          </Link>
          .
        </p>
      </div>
    </div>
  );
}
