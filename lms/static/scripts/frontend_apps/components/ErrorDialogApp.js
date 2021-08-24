import { Fragment, createElement } from 'preact';
import { useContext } from 'preact/hooks';

import { Config } from '../config';

import ErrorDisplay from './ErrorDisplay';
import Dialog from './Dialog';

/**
 * A general-purpose error dialog displayed when a frontend application cannot be launched.
 *
 * There are more specific error dialogs for some use cases (eg. OAuth2RedirectErrorApp).
 */
export default function ErrorDialogApp() {
  const {
    errorDialog: { errorCode, errorDetails = '' },
  } = useContext(Config);

  const error = { code: errorCode, details: errorDetails };

  let title;
  let message;

  switch (errorCode) {
    case 'reused_tool_guid':
      title = 'Consumer key registered with another site';
      message = 'Reused tool_consumer_instance_guid';
      break;
    default:
      title = 'An error occurred';
      message = 'Unknown error occurred';
  }

  return (
    <Dialog title={title}>
      {error.code === 'reused_tool_guid' && (
        <Fragment>
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
        </Fragment>
      )}
      <ErrorDisplay message={message} error={error} />
    </Dialog>
  );
}
