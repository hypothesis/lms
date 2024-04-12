import { Link } from '@hypothesis/frontend-shared';

import { useConfig } from '../config';
import ErrorModal from './ErrorModal';

/**
 * A general-purpose error dialog displayed when a frontend application cannot be launched.
 *
 * This is rendered as a non-closeable Modal. It cannot be dismissed.
 *
 * There are more specific error dialogs for some use cases
 * (e.g. OAuth2RedirectErrorApp, LaunchErrorDialog).
 */
export default function ErrorDialogApp() {
  const { errorDialog } = useConfig(['errorDialog']);

  const error = {
    errorCode: errorDialog.errorCode,
    details: errorDialog.errorDetails ?? '',
    message: errorDialog.errorMessage ?? '',
  };

  let description;
  let title;

  let displaySupportLink = true;

  switch (error.errorCode) {
    case 'reused_consumer_key':
      title = 'Consumer key registered with another site';
      break;
    case 'vitalsource_student_pay_no_license':
      title = 'Missing license for H';
      break;
    case 'vitalsource_student_pay_license_launch':
      title = 'Acquired Hypothesis license';
      displaySupportLink = false;
      break;
    default:
      description =
        'An error occurred when launching the Hypothesis application';
      title = 'An error occurred';
  }

  return (
    <ErrorModal
      description={description}
      error={error}
      title={title}
      displaySupportLink={displaySupportLink}
    >
      {error.errorCode === 'reused_consumer_key' && (
        <>
          <p>
            This Hypothesis {"installation's"} consumer key appears to have
            already been used on another site. This could be because:
          </p>
          <ul className="px-4 list-disc">
            <li>
              This consumer key has already been used on another site. A site
              admin must{' '}
              <Link
                target="_blank"
                href="https://web.hypothes.is/get-help/"
                underline="none"
              >
                request a new consumer key
              </Link>{' '}
              for this site and re-install Hypothesis.
            </li>
            <li>
              This {"site's"} tool_consumer_instance_guid has changed. A site
              admin must{' '}
              <Link
                target="_blank"
                href="https://web.hypothes.is/get-help/"
                underline="none"
              >
                ask us to update the consumer key
              </Link>
              .
            </li>
          </ul>
        </>
      )}
      {error.errorCode === 'vitalsource_student_pay_no_license' && (
        <>
          <p>
            You {"don't"} have license from VitalSource for the Hypothesis app.
          </p>
        </>
      )}
      {error.errorCode === 'vitalsource_student_pay_license_launch' && (
        <>
          <p>You now have a license for Hypothesis.</p>
        </>
      )}
    </ErrorModal>
  );
}
