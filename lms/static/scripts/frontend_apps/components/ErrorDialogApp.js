import { Link } from '@hypothesis/frontend-shared';
import { useContext } from 'preact/hooks';

import { Config } from '../config';

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
  const { errorDialog } = useContext(Config);

  const error = {
    errorCode: errorDialog?.errorCode,
    details: errorDialog?.errorDetails ?? '',
  };

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
    <ErrorModal description={description} error={error} title={title}>
      {error.errorCode === 'reused_consumer_key' && (
        <>
          <p>
            This Hypothesis {"installation's"} consumer key appears to have
            already been used on another site. This could be because:
          </p>
          <ul className="u-list">
            <li>
              This consumer key has already been used on another site. A site
              admin must{' '}
              <Link target="_blank" href="https://web.hypothes.is/get-help/">
                request a new consumer key
              </Link>{' '}
              for this site and re-install Hypothesis.
            </li>
            <li>
              This {"site's"} tool_consumer_instance_guid has changed. A site
              admin must{' '}
              <Link target="_blank" href="https://web.hypothes.is/get-help/">
                ask us to update the consumer key
              </Link>
              .
            </li>
          </ul>
        </>
      )}
    </ErrorModal>
  );
}
