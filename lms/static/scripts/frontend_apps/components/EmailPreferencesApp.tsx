import {
  Button,
  InfoIcon,
  Link,
  Panel,
  ToastMessages,
  useToastMessages,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useCallback, useState } from 'preact/hooks';

import type { SelectedDays, WeekDay } from '../config';
import { useConfig } from '../config';
import EmailDigestPreferences from './EmailDigestPreferences';
import EmailMentionsPreferences from './EmailMentionsPreferences';

export default function EmailPreferencesApp() {
  const { emailPreferences } = useConfig(['emailPreferences']);
  const [selectedDays, setSelectedDays] = useState(
    emailPreferences.selectedDays,
  );
  const selectedDaysChanged = useCallback(
    (newSelectedDays: Partial<SelectedDays>) =>
      Object.entries(newSelectedDays).some(
        ([day, selected]) =>
          emailPreferences.selectedDays[day as WeekDay] !== selected,
      ),
    [emailPreferences.selectedDays],
  );
  const [saving, setSaving] = useState(false);
  const onSave = useCallback(() => setSaving(true), []);
  const { toastMessages, dismissToastMessage } = useToastMessages(
    emailPreferences.flashMessage
      ? [
          {
            message: emailPreferences.flashMessage,
            type: 'success',
          },
        ]
      : [],
  );
  const updateSelectedDays = useCallback(
    (newSelectedDays: Partial<SelectedDays>) => {
      setSelectedDays(prev => ({ ...prev, ...newSelectedDays }));

      // Dismiss toast message if visible and selection actually changed
      // compared to initial value
      if (toastMessages[0] && selectedDaysChanged(newSelectedDays)) {
        dismissToastMessage(toastMessages[0].id);
      }
    },
    [dismissToastMessage, selectedDaysChanged, toastMessages],
  );

  return (
    <div className="min-h-full bg-grey-2">
      <div
        className={classnames(
          'flex justify-center p-3 w-full',
          'bg-white border-b shadow',
        )}
      >
        <img
          alt="Hypothesis logo"
          src="/static/images/hypothesis-wordmark-logo.png"
          className="h-10"
        />
      </div>
      <div className="absolute top-20 w-full flex justify-center">
        <div className="w-80">
          <ToastMessages
            messages={toastMessages}
            onMessageDismiss={dismissToastMessage}
          />
        </div>
      </div>
      <div className="flex flex-col gap-y-4 pb-8 pt-4 md:pt-8 px-4">
        <form
          method="post"
          onSubmit={onSave}
          className="flex flex-col gap-3 mx-auto max-w-[450px]"
        >
          <Panel
            title="Email notifications"
            fullWidthHeader
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
            <div className="flex flex-col gap-y-8">
              {emailPreferences.is_instructor && (
                <EmailDigestPreferences
                  selectedDays={selectedDays}
                  onSelectedDaysChange={updateSelectedDays}
                />
              )}
              {emailPreferences.mention_email_feature_enabled && (
                <EmailMentionsPreferences
                  subscribed={emailPreferences.mention_email_subscribed}
                />
              )}
            </div>
          </Panel>
        </form>
        <p className="text-center text-grey-8">
          <InfoIcon className="inline" /> Do you need help? Visit our{' '}
          <Link
            variant="custom"
            underline="always"
            href="https://web.hypothes.is/help/"
            target="_blank"
          >
            help center
          </Link>
          .
        </p>
      </div>
    </div>
  );
}
