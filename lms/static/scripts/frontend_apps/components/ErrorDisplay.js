import { Link, Scrollbox } from '@hypothesis/frontend-shared';

import { formatErrorDetails, formatErrorMessage } from '../errors';

/**
 * @typedef {import('../errors').ErrorLike} ErrorLike
 */

/**
 * Adds punctuation to a string if missing.
 *
 * @param {string} str
 */
function toSentence(str) {
  return str.match(/[.!?]$/) ? str : str + '.';
}

/**
 * @typedef ErrorDetailsProps
 * @prop {ErrorLike} error
 */

/**
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
    <details
      className="hyp-u-border"
      onToggle={onDetailsToggle}
      data-testid="error-details"
    >
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
function supportURL(errorMessage, error) {
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
  const message = formatErrorMessage(error, /* prefix */ description);

  return (
    <Scrollbox classes="LMS-Scrollbox">
      <div className="hyp-u-vertical-spacing hyp-u-padding--top--4">
        {message && <p data-testid="error-message">{toSentence(message)}</p>}

        {children}
        <p data-testid="error-links">
          If the problem persists, you can{' '}
          <Link href={supportURL(message, error)} target="_blank">
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
