import propTypes from 'prop-types';
import { Fragment, createElement } from 'preact';

function emailLink({ address, subject = '', body = '' }) {
  return `mailto:${address}?subject=${encodeURIComponent(
    subject
  )}&body=${encodeURIComponent(body)}`;
}

/**
 * Displays details of an error, such as a failed API call and provide the user
 * with information on how to get help with it.
 */
export default function ErrorDisplay({ message, error }) {
  let details = '';

  if (typeof error.details === 'object') {
    try {
      details = JSON.stringify(error.details, null, 2 /* indent */);
    } catch (e) {
      // ignore
    }
  } else {
    details = error.details;
  }

  const supportLink = emailLink({
    address: 'support@hypothes.is',
    subject: 'Hypothesis LMS support',
    body: `

Error message: ${error.message}

Technical details:

${details}
    `,
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
          {message}
          {error.message && (
            <Fragment>
              : <i>{error.message}</i>
            </Fragment>
          )}
        </p>
      )}
      <p>
        If the problem persists{' '}
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

ErrorDisplay.propTypes = {
  /**
   * A short message explaining that a problem happened.
   */
  message: propTypes.oneOfType([propTypes.string, propTypes.element]),

  /**
   * An `Error`-like object with details of the problem.
   *
   * This is assumed to have a string `message` property and may have a
   * JSON-serializable `details` property.
   */
  error: propTypes.object.isRequired,
};
