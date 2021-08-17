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
      title =
        'The Hypothesis credentials your install is using may have already been used in a different LMS instance';
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
          This may be due to one of the following:
          <ul>
            <li>
              The same Hypothesis Consumer Key and Shared Secret has been used
              previously in another LMS instance
            </li>
            <li>
              The{' '}
              <a
                target="_blank"
                rel="noopener noreferrer"
                href="https://www.imsglobal.org/specs/ltiv1p1p1/implementation-guide"
              >
                tool_consumer_instance_guid
              </a>{' '}
              of your LMS has changed
            </li>
          </ul>
        </Fragment>
      )}
      <ErrorDisplay message={message} error={error} />
    </Dialog>
  );
}
