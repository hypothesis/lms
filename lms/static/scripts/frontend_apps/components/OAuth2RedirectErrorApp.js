import { Link } from '@hypothesis/frontend-shared';
import { useContext } from 'preact/hooks';

import { Config } from '../config';

import ErrorModal from './ErrorModal';

/** @typedef {import('../config').OAuthErrorConfig} OAuthErrorConfig */

/**
 * @typedef OAuth2RedirectErrorAppProps
 * @prop {Location} [location] - Test seam
 */

/**
 * Error Modal displayed when authorization with a third-party API via OAuth
 * fails.
 *
 * Dismissing the Modal will close the window.
 *
 * @param {OAuth2RedirectErrorAppProps} props
 */
export default function OAuth2RedirectErrorApp({ location = window.location }) {
  const { OAuth2RedirectError = /** @type {OAuthErrorConfig} */ ({}) } =
    useContext(Config);

  const {
    authUrl = null,
    errorCode,
    errorDetails = '',
    canvasScopes = /** @type {string[]} */ ([]),
  } = OAuth2RedirectError ?? {};

  const error = { errorCode, details: errorDetails };

  let title;
  let description;
  switch (errorCode) {
    case 'canvas_invalid_scope':
      title = 'Developer key scopes missing';
      break;
    case 'blackboard_missing_integration':
      title = 'Missing Blackboard REST API integration';
      break;
    default:
      title = 'Authorization failed';
      description = 'Something went wrong when authorizing Hypothesis';
      break;
  }

  const retry = () => {
    location.href = /** @type {string} */ (authUrl);
  };
  const onRetry = authUrl ? retry : undefined;

  return (
    <ErrorModal
      cancelLabel="Close"
      contentClass="LMS-Dialog LMS-Dialog--wide"
      description={description}
      error={error}
      onCancel={() => window.close()}
      onRetry={onRetry}
      title={title}
    >
      {errorCode === 'canvas_invalid_scope' && (
        <>
          <p>
            A Canvas admin needs to edit {"Hypothesis's"} developer key and add
            these scopes:
          </p>
          <ol>
            {canvasScopes.map(scope => (
              <li key={scope}>
                <code>{scope}</code>
              </li>
            ))}
          </ol>
          <p>
            For more information see:{' '}
            <Link
              target="_blank"
              href="https://github.com/hypothesis/lms/wiki/Canvas-API-Endpoints-Used-by-the-Hypothesis-LMS-App"
            >
              Canvas API Endpoints Used by the Hypothesis LMS App
            </Link>
            .
          </p>
        </>
      )}

      {errorCode === 'blackboard_missing_integration' && (
        <>
          <p>
            In order to allow Hypothesis to connect to files in Blackboard, your
            Blackboard admin needs to add or enable a REST API integration.
          </p>
          <p>
            For more information, please have your Blackboard admin read:{' '}
            <Link
              target="_blank"
              href="https://web.hypothes.is/help/enable-the-hypothesis-integration-with-blackboard-files/"
            >
              Enable the Hypothesis Integration With Blackboard Files
            </Link>
            .
          </p>
        </>
      )}
    </ErrorModal>
  );
}
