import { Checkbox } from '@hypothesis/frontend-shared';
import classnames from 'classnames';

export type EmailMentionsPreferencesProps = {
  subscribed: boolean;
};

export default function EmailMentionsPreferences({
  subscribed,
}: EmailMentionsPreferencesProps) {
  return (
    <div className="flex flex-col gap-y-3">
      <h2 className="text-lg/6 text-brand">Mentions</h2>
      <p>
        Receive email notifications when you are mentioned in an annotation.
      </p>
      <div className="px-4">
        <span
          className={classnames(
            // The checked icon sets fill from the text color
            'text-grey-6',
          )}
        >
          <Checkbox
            name="mention_email_subscribed"
            defaultChecked={subscribed}
            data-testid="mentions-checkbox"
          >
            <span
              className={classnames(
                // Override the color set for the checkbox fill
                'text-grey-9',
              )}
            >
              Receive mention notifications
            </span>
          </Checkbox>
        </span>
      </div>
    </div>
  );
}
