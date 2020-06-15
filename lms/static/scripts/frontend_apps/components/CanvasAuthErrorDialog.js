import { Fragment, createElement } from 'preact';
import propTypes from 'prop-types';

import Button from './Button';
import ErrorDisplay from './ErrorDisplay';
import Dialog from './Dialog';

/**
 * Error dialog displayed when authorization of Canvas API access via OAuth
 * fails.
 */
export default function CanvasAuthErrorDialog({
  details,
  invalidScope,
  scopes,
  authorizeUrl,
}) {
  const title = invalidScope
    ? 'Developer key scopes missing'
    : 'Authorization failed';

  const retry = () => (window.location.href = authorizeUrl);

  const message = invalidScope
    ? null
    : 'Something went wrong when authorizing Hypothesis';

  const error = { details };

  return (
    <Dialog
      title={title}
      onCancel={() => window.close()}
      buttons={
        authorizeUrl
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

CanvasAuthErrorDialog.propTypes = {
  authorizeUrl: propTypes.string,
  details: propTypes.string,
  invalidScope: propTypes.bool,
  scopes: propTypes.arrayOf(propTypes.string),
};
