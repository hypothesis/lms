import { useContext } from 'preact/hooks';
import { Modal } from '@hypothesis/frontend-shared';

import { Config } from '../config';
import { AppConfigError } from '../errors';

import ErrorDisplay from './ErrorDisplay';

/**
 * A general-purpose error dialog displayed when a frontend application cannot be launched.
 *
 * This is rendered as a non-closeable Modal. It cannot be dismissed.
 *
 * There are more specific error dialogs for some use cases
 * (e.g. OAuth2RedirectErrorApp, LaunchErrorDialog).
 */
export default function ErrorDialogApp() {
  const { errorDialog } = useContext(Config);

  const error = new AppConfigError({
    errorCode: errorDialog?.errorCode,
    errorDetails: errorDialog?.errorDetails ?? '',
  });

  let description;
  let title;

  switch (error.errorCode) {
    case 'reused_consumer_key':
      title = 'Consumer key registered with another site';
      break;
    default:
      description =
        'An error occurred when launching the Hypothesis application';
      title = 'An error occurred';
  }

  return (
    <Modal
      onCancel={() => null}
      title={title}
      withCloseButton={false}
      withCancelButton={false}
      contentClass="LMS-Dialog LMS-Dialog--medium"
    >
      <ErrorDisplay error={error} description={description}>
        {error.errorCode === 'reused_consumer_key' && (
          <>
            <p>
              This Hypothesis {"installation's"} consumer key appears to have
              already been used on another site. This could be because:
            </p>
            <ul>
              <li>
                This consumer key has already been used on another site. A site
                admin must{' '}
                <a
                  target="_blank"
                  rel="noopener noreferrer"
                  href="https://web.hypothes.is/get-help/"
                >
                  request a new consumer key
                </a>{' '}
                for this site and re-install Hypothesis.
              </li>
              <li>
                This {"site's"} tool_consumer_instance_guid has changed. A site
                admin must{' '}
                <a
                  target="_blank"
                  rel="noopener noreferrer"
                  href="https://web.hypothes.is/get-help/"
                >
                  ask us to update the consumer key
                </a>
                .
              </li>
            </ul>
          </>
        )}
      </ErrorDisplay>
    </Modal>
  );
}
