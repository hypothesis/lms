import { Fragment, createElement } from 'preact';
import { useContext } from 'preact/hooks';
import propTypes from 'prop-types';

import { Config } from '../config';

import Button from './Button';
import ErrorDisplay from './ErrorDisplay';
import Dialog from './Dialog';

/**
 * Error dialog displayed when authorization of Canvas API access via OAuth
 * fails.
 */
export default function CanvasOAuth2RedirectErrorApp({
  location = window.location,
}) {
  const {
    canvasOAuth2RedirectError: {
      authorizeUrl = null,
      invalidScope = false,
      errorDetails = '',
      scopes = [],
    },
  } = useContext(Config);

  const title = invalidScope
    ? 'Developer key scopes missing'
    : 'Authorization failed';

  const message = invalidScope
    ? null
    : 'Something went wrong when authorizing Hypothesis';

  const error = { details: errorDetails };

  const retry = () => {
    location.href = /** @type {string} */ (authorizeUrl);
  };

  const buttons = [
    <Button
      className="Button--cancel"
      key="close"
      label="Close"
      onClick={() => window.close()}
    />,
  ];

  if (authorizeUrl) {
    buttons.push(<Button key="try-again" label="Try again" onClick={retry} />);
  }

  return (
    <Dialog title={title} buttons={buttons}>
      {invalidScope && (
        <Fragment>
          <p>
            A Canvas admin needs to edit {"Hypothesis's"} developer key and add
            these scopes:
          </p>
          <ol>
            {scopes.map(scope => (
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
      <ErrorDisplay message={message} error={error} />
    </Dialog>
  );
}

CanvasOAuth2RedirectErrorApp.propTypes = {
  // Test seam for `window.location`.
  location: propTypes.object,
};
