/**
 * Generate a `mailto:` URL that prompts to send an email with pre-filled fields.
 *
 * @param {object} args
 * @param {string} args.address - Email address to sent to
 * @param {string} [args.subject] - Pre-filled subject line
 * @param {string} [args.body] - Pre-filled body
 */
function emailLink({ address, subject = '', body = '' }) {
  return `mailto:${address}?subject=${encodeURIComponent(
    subject
  )}&body=${encodeURIComponent(body)}`;
}

/**
 * Adds punctuation to a string if missing.
 *
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
 * @prop {object|string} [details] - Optional JSON-serializable details of the error
 */

/**
 * JSON-stringify `error.details` if it is extant and an object
 *
 * @param {ErrorLike} error
 */
function formatErrorDetails(error) {
  /** @type {string|object} */
  let details = error.details ?? '';
  if (error?.details && typeof error.details === 'object') {
    try {
      details = JSON.stringify(error.details, null, 2 /* indent */);
    } catch (e) {
      // ignore
    }
  }
  return details;
}

/**
 * @typedef ErrorDetailsProps
 * @prop {ErrorLike} error
 *
 * Render pre-formatted JSON details of an error
 *
 * @param {ErrorDetailsProps} props
 */
function ErrorDetails({ error }) {
  /** @param {Event} event */
  const onDetailsToggle = event => {
    const detailsEl = /** @type {HTMLDetailsElement} */ (event.target);
    if (!detailsEl.open) {
      return;
    }
    detailsEl.scrollIntoView({ behavior: 'smooth' });
  };

  const details = formatErrorDetails(error);
  if (!details) {
    return null;
  }

  return (
    <details className="ErrorDisplay__details" onToggle={onDetailsToggle}>
      <summary className="ErrorDisplay__details-summary">Error Details</summary>
      <pre className="ErrorDisplay__details-content">{details}</pre>
    </details>
  );
}

/**
 * @typedef ErrorDisplayProps
 * @prop {string|null} [message] -
 *   A short message to display explaining that a problem happened. This is
 *   typically a general message like "There was a problem fetching this assignment".
 *   In cases where the the error originates from the server, this message may not
 *   be necessary, but in other cases where the `error.message` is generic and perhaps
 *   originates from an exception in the client, then this prop can be used to
 *   provide additional specifics.
 * @prop {ErrorLike} error -
 *   An `Error`-like object with specific details of the problem. If `error` contains
 *   a `message` property, then that string will be rendered.
 */

/**
 * Displays details of an error, such as a failed API call and provide the user
 * with information on how to get help with it.
 *
 * @param {ErrorDisplayProps} props
 */
export default function ErrorDisplay({ message, error }) {
  const details = formatErrorDetails(error);

  const supportLink = emailLink({
    address: 'support@hypothes.is',
    subject: 'Hypothesis LMS support',
    body: `
Error message: ${error?.message || 'N/A'}
Description: ${description || 'N/A'}
Technical details: ${details || 'N/A'}
    `,
  });

  return (
    <div className="ErrorDisplay">
      {message && (
        <p data-testid="message">
          {message}
          {error.message && (
            <>
              : <i>{toSentence(error.message)}</i>
            </>
          )}
        </p>
      )}
      <p className="ErrorDisplay__links">
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
      <ErrorDetails error={error} />
    </div>
  );
}
