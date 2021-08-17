import { LabeledButton } from '@hypothesis/frontend-shared';
import { Fragment, createElement } from 'preact';
import { useContext } from 'preact/hooks';

import { Config } from '../config';

import ErrorDisplay from './ErrorDisplay';
import Dialog from './Dialog';

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
  const {
    OAuth2RedirectError: {
      authUrl = /** @type {string|null} */ (null),
      errorCode = /** @type {string|null} */ (null),
      errorDetails = '',
      canvasScopes = /** @type {string[]} */ ([]),
    },
  } = useContext(Config);

  const error = { code: errorCode, details: errorDetails };

  const title = (() => {
    if (errorCode === 'canvas_invalid_scope') {
      return 'Developer key scopes missing';
    }

    if (errorCode === 'blackboard_missing_integration') {
      return 'Missing Blackboard REST API integration';
    }

    return 'Authorization failed';
  })();

  const message = 'Something went wrong when authorizing Hypothesis';

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
        <Fragment>
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
        </Fragment>
      )}

      {error.code === 'blackboard_missing_integration' && (
        <Fragment>
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
        </Fragment>
      )}
      <ErrorDisplay message={message} error={error} />
    </Dialog>
  );
}
