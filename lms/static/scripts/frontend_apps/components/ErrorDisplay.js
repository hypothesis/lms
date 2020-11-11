import { Fragment, createElement } from 'preact';

function emailLink({ address, subject = '', body = '' }) {
  return `mailto:${address}?subject=${encodeURIComponent(
    subject
  )}&body=${encodeURIComponent(body)}`;
}

/**
 * @param {string} str
 */
function toSentence(str) {
  return str.match(/[.!?]$/) ? str : str + '.';
}

/**
 * An `Error` or `Error`-like object.
 *
 * @typedef ErrorLike
 * @prop {string} [message]
 * @prop {Object} [details] - Optional JSON-serializable details of the error
 */

/**
 * @typedef ErrorDisplayProps
 * @prop {string|null} [message] -
 *   A short message to display explaining that a problem happened. This is
 *   typically a general message like "There was a problem fetching this assignment".
 * @prop {ErrorLike} error -
 *   An `Error`-like object with specific details of the problem
 */

/**
 * Displays details of an error, such as a failed API call and provide the user
 * with information on how to get help with it.
 *
 * @param {ErrorDisplayProps} props
 */
export default function ErrorDisplay({ message, error }) {
  let details = '';

  if (typeof error.details === 'object' && error.details !== null) {
    try {
      details = JSON.stringify(error.details, null, 2 /* indent */);
    } catch (e) {
      // ignore
    }
  } else {
    details = error.details;
  }

  let supportEmailBody = '';
  if (error.message) {
    supportEmailBody += `\n\nError message: ${error.message}`;
  }
  if (details) {
    supportEmailBody += `\n\nTechnical details:\n\n${details}`;
  }

  const supportLink = emailLink({
    address: 'support@hypothes.is',
    subject: 'Hypothesis LMS support',
    body: supportEmailBody,
  });

  const onDetailsToggle = event => {
    const details = event.target;
    if (!details.open) {
      return;
    }
    details.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    // nb. Wrapper `<div>` here exists to apply block layout to contents.
    <div className="ErrorDisplay">
      {message && (
        <p>
          {!error.message && toSentence(message)}
          {error.message && (
            <Fragment>
              {message}: <i>{toSentence(error.message)}</i>
            </Fragment>
          )}
        </p>
      )}
      <p>
        If the problem persists,{' '}
        <a href={supportLink} target="_blank" rel="noopener noreferrer">
          send us an email
        </a>{' '}
        or{' '}
        <a
          href="https://web.hypothes.is/get-help/"
          target="_blank"
          rel="noopener noreferrer"
        >
          open a support ticket
        </a>
        . You can also visit our{' '}
        <a
          href="https://web.hypothes.is/help/"
          target="_blank"
          rel="noopener noreferrer"
        >
          help documents
        </a>
        .
      </p>
      {!!details && (
        <details className="ErrorDisplay__details" onToggle={onDetailsToggle}>
          <summary className="ErrorDisplay__details-summary">
            Error Details
          </summary>
          <pre className="ErrorDisplay__details-content">{details}</pre>
        </details>
      )}
    </div>
  );
}
