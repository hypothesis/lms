import { LabeledButton } from '@hypothesis/frontend-shared';
import { useContext } from 'preact/hooks';

import { Config } from '../config';

import ErrorDisplay from './ErrorDisplay';
import Dialog from './Dialog';

/** @typedef {import('../config').OAuthErrorConfig} OAuthErrorConfig */

/**
 * @typedef OAuth2RedirectErrorAppProps
 * @prop {Location} [location] - Test seam
 */

/**
 * Error dialog displayed when authorization with a third-party API via OAuth
 * fails.
 *
 * @param {OAuth2RedirectErrorAppProps} props
 */
export default function OAuth2RedirectErrorApp({ location = window.location }) {
  const { OAuth2RedirectError = /** @type {OAuthErrorConfig} */ ({}) } =
    useContext(Config);

  const {
    authUrl = null,
    errorCode = null,
    errorDetails = '',
    canvasScopes = /** @type {string[]} */ ([]),
  } = OAuth2RedirectError ?? {};

  const error = { code: errorCode, details: errorDetails };

  let title;
  let message;
  switch (errorCode) {
    case 'canvas_invalid_scope':
      title = 'Developer key scopes missing';
      break;
    case 'blackboard_missing_integration':
      title = 'Missing Blackboard REST API integration';
      break;
    default:
      title = 'Authorization failed';
      message = 'Something went wrong when authorizing Hypothesis';
      break;
  }

  const retry = () => {
    location.href = /** @type {string} */ (authUrl);
  };

  const buttons = [
    <LabeledButton
      key="close"
      onClick={() => window.close()}
      data-testid="close"
    >
      Close
    </LabeledButton>,
  ];

  if (authUrl) {
    buttons.push(
      <LabeledButton
        key="try-again"
        onClick={retry}
        data-testid="try-again"
        variant="primary"
      >
        Try again
      </LabeledButton>
    );
  }

  return (
    <Dialog title={title} buttons={buttons}>
      {error.code === 'canvas_invalid_scope' && (
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
            <a
              target="_blank"
              rel="noopener noreferrer"
              href="https://github.com/hypothesis/lms/wiki/Canvas-API-Endpoints-Used-by-the-Hypothesis-LMS-App"
            >
              Canvas API Endpoints Used by the Hypothesis LMS App
            </a>
            .
          </p>
        </>
      )}

      {error.code === 'blackboard_missing_integration' && (
        <>
          <p>
            In order to allow Hypothesis to connect to files in Blackboard, your
            Blackboard admin needs to add or enable a REST API integration.
          </p>
          <p>
            For more information, please have your Blackboard admin read:{' '}
            <a
              target="_blank"
              rel="noopener noreferrer"
              href="https://web.hypothes.is/help/enable-the-hypothesis-integration-with-blackboard-files/"
            >
              Enable the Hypothesis Integration With Blackboard Files
            </a>
            .
          </p>
        </>
      )}
      <ErrorDisplay message={message} error={error} />
    </Dialog>
  );
}
