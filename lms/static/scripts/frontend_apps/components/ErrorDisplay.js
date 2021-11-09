import { Scrollbox } from '@hypothesis/frontend-shared';

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
 * An `Error` or `Error`-like object. This allows this component to be used
 * by just passing through an `Error` without meddling with it, or manual
 * control of `message` and/or `details` if so desired.
 *
 * @typedef ErrorLike
 * @prop {string} [message]
 * @prop {object|string} [details] - Optional JSON-serializable details of the error
 * @prop {string} [serverMessage] - Explanatory message provided by backend that
 *   will be preferred over `message` if it is present.
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
    <details className="hyp-u-border" onToggle={onDetailsToggle}>
      <summary className="hyp-u-bg-color--grey-1 hyp-u-padding ErrorDetails__summary">
        Error Details
      </summary>
      <pre className="hyp-u-padding hyp-u-margin--0 ErrorDetails__details">
        {details}
      </pre>
    </details>
  );
}

/**
 * @typedef {import("preact").ComponentChildren} Children
 *
 * @typedef ErrorDisplayProps
 * @prop {Children} [children]
 * @prop {string|null} [description] -
 *   A short message explaining the error and its human-facing relevance, provided
 *   by this (front-end) app for context.
 * @prop {ErrorLike} error - Error-like object containing further `details`
 *   or `message` about this error state. The value of `details` and `message`
 *   may come from a server response.
 */

/**
 * Displays human-facing details of an error
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

  // If `serverMessage` is extant on `error`, prefer it to `error.message` even
  // if `serverMessage` is empty — In cases where we are displaying error
  // information provided by the backend (i.e. `APIError`), we do not want
  // to render the JS Error instance's `message` as it likely does not apply
  const message = error.serverMessage ?? error.message;

  return (
    <Scrollbox classes="LMS-Scrollbox">
      <div className="hyp-u-vertical-spacing hyp-u-padding--top--4">
        {message && !description && (
          <p data-testid="error-message">
            <i>{toSentence(message)}</i>
          </p>
        )}
        {message && description && (
          <p data-testid="error-message">
            {description}: <i>{toSentence(message)}</i>
          </p>
        )}
        {!message && description && (
          <p data-testid="error-message">{toSentence(description)}</p>
        )}

        {children}
        <p data-testid="error-links">
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
    </Scrollbox>
  );
}
