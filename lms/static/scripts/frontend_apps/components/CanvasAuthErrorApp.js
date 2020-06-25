import { Fragment, createElement } from 'preact';
import { useContext } from 'preact/hooks';

import { Config } from '../config';

import Button from './Button';
import ErrorDisplay from './ErrorDisplay';
import Dialog from './Dialog';

/**
 * Error dialog displayed when authorization of Canvas API access via OAuth
 * fails.
 */
export default function CanvasAuthErrorApp() {
  const {
    authUrl,
    invalidScope = false,
    errorDetails = '',
    scopes = [],
  } = useContext(Config);

  const title = invalidScope
    ? 'Developer key scopes missing'
    : 'Authorization failed';

  const retry = () => (window.location.href = authUrl);

  const message = invalidScope
    ? null
    : 'Something went wrong when authorizing Hypothesis';

  const error = { details: errorDetails };

  return (
    <Dialog
      title={title}
      onCancel={() => window.close()}
      buttons={
        authUrl
          ? [<Button key="try-again" onClick={retry} label="Try again" />]
          : []
      }
    >
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

CanvasAuthErrorApp.propTypes = {};
