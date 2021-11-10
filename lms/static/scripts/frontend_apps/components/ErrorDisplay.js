import { Link, Scrollbox } from '@hypothesis/frontend-shared';

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
 * @prop {string} [errorCode] - Provided by back-end to identify error state
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
 * Prepare a URL that will pre-fill a support form with certain details
 * about the current error.
 *
 * @param {string} errorMessage
 * @param {ErrorLike} error
 * @returns {string}
 */
function formatSupportURL(errorMessage, error) {
  const supportURL = new URL('https://web.hypothes.is/get-help/');

  supportURL.searchParams.append('product', 'LMS_app');
  supportURL.searchParams.append(
    'subject',
    errorMessage
      ? `(LMS Error) ${errorMessage}`
      : 'Error encountered in Hypothesis LMS Application'
  );

  const details = formatErrorDetails(error);
  if (error.errorCode || details) {
    const content = `
----------------------
Feel free to add additional details above about the problem you are experiencing.
The error information below helps our team pinpoint the issue faster.
----------------------
Error code: ${error.errorCode ?? 'N/A'}
Details: ${formatErrorDetails(error) || 'N/A'}
  `;
    supportURL.searchParams.append('content', content);
  }
  return supportURL.toString();
}

/**
 * @typedef {import("preact").ComponentChildren} Children
 *
 * @typedef ErrorDisplayProps
 * @prop {Children} [children]
 * @prop {string} [description] -
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
export default function ErrorDisplay({ children, description = '', error }) {
  // If `serverMessage` is extant on `error`, prefer it to `error.message` even
  // if `serverMessage` is empty — In cases where we are displaying error
  // information provided by the backend (i.e. `APIError`), we do not want
  // to render the JS Error instance's `message` as it likely does not apply
  const message = error.serverMessage ?? error.message ?? '';

  // Create an error status message from the combination of `description` and
  // `message`. As neither of these are guaranteed to be present, the
  // resulting string may be empty.
  const errorMessage = `${description}${
    description && message ? ': ' : ''
  }${message}`;

  return (
    <Scrollbox classes="LMS-Scrollbox">
      <div className="hyp-u-vertical-spacing hyp-u-padding--top--4">
        {errorMessage && (
          <p data-testid="error-message">{toSentence(errorMessage)}</p>
        )}

        {children}
        <p data-testid="error-links">
          If the problem persists, you can{' '}
          <Link href={formatSupportURL(errorMessage, error)} target="_blank">
            open a support ticket
          </Link>{' '}
          or visit our{' '}
          <Link href="https://web.hypothes.is/help/" target="_blank">
            help documents
          </Link>
          .
        </p>
        <ErrorDetails error={error} />
      </div>
    </Scrollbox>
  );
}
