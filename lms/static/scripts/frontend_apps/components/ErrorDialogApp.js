import { useContext } from 'preact/hooks';

import { Config } from '../config';

import ErrorDisplay from './ErrorDisplay';
import Dialog from './Dialog';

/**
 * A general-purpose error dialog displayed when a frontend application cannot be launched.
 *
 * There are more specific error dialogs for some use cases
 * (e.g. OAuth2RedirectErrorApp, LaunchErrorDialog).
 */
export default function ErrorDialogApp() {
  const { errorDialog } = useContext(Config);

  const error = {
    code: errorDialog?.errorCode,
    details: errorDialog?.errorDetails ?? '',
  };

  let title;

  switch (error.code) {
    case 'reused_consumer_key':
      title = 'Consumer key registered with another site';
      break;
    default:
      title = 'An error occurred';
  }

  return (
    <Dialog title={title}>
      {error.code === 'reused_consumer_key' ? (
        <>
          This Hypothesis installation&apos;s consumer key appears to have
          already been used on another site. This could be because:
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
              This site&apos;s tool_consumer_instance_guid has changed. A site
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
          <ErrorDisplay error={error} />
        </>
      ) : (
        <ErrorDisplay
          error={error}
          description="An error occurred when launching the Hypothesis application"
        />
      )}
    </Dialog>
  );
}
