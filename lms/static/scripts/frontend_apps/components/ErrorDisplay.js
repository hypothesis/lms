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
 * @typedef {import("preact").ComponentChildren} Children
 *
 * @typedef ErrorDisplayProps
 * @prop {Children} [children]
 * @prop {string|null} [description] -
 *   A short message explaining the error and its human-facing relevance.
 *   This is typically a general message like
 *   "There was a problem fetching this assignment". This description
 *   always comes from (this) LMS client app.
 *
 *   The presence of a `description` indicates that this `ErrorDisplay` is
 *   responsible for explaining the error to the user in some fashion. Along
 *   with this `description`, anything available in `error.message` is also
 *   shown.
 *
 *   When `description` is absent, it indicates that the main explaining of
 *   the error's relevance to the user is handled elsewhere, and no additional
 *   error messaging is necessary. This is the case, for example, with some
 *   of the well-explained error states in `OAuth2RedirectErrorApp` or
 *   `LaunchErrorDialog`: these don't need additional error messaging that is,
 *   for the most part, redundant or useless.
 *
 *   Available `error.details` and support/email instructions are always
 *   shown regardless of the presence of this prop.
 *
 * @prop {ErrorLike} error - Error-like object containing further `details`
 *   or `message` about this error state. The value of `details` and `message`
 *   may come from a server response.
 */

/**
 * Displays human-facing details of an error, including:
 * - Explanation/message (if `description` is provided)
 * - Instructions for contacting support and getting help
 * - Stringified-JSON details of the error (if `error.details` is populated)
 *
 * @param {ErrorDisplayProps} props
 */
export default function ErrorDisplay({ children, description, error }) {
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
      {children}
      {description && (
        <p data-testid="message">
          {description}
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
