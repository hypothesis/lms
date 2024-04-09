import { Link, Scroll } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { ComponentChildren } from 'preact';

import { formatErrorDetails, formatErrorMessage } from '../errors';
import type { ErrorLike } from '../errors';

/**
 * Adds punctuation to a string if missing.
 */
function toSentence(str: string): string {
  return str.match(/[.!?]$/) ? str : str + '.';
}

type ErrorDetailsProps = {
  error: ErrorLike;
};

/**
 * Render pre-formatted JSON details of an error
 */
function ErrorDetails({ error }: ErrorDetailsProps) {
  const onDetailsToggle = (event: Event) => {
    const detailsEl = event.target as HTMLDetailsElement;
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
      className="border rounded overflow-hidden"
      onToggle={onDetailsToggle}
      data-testid="error-details"
    >
      <summary
        className={classnames(
          'sticky top-0',
          'bg-grey-1 p-2 cursor-pointer',
          'focus-visible-ring ring-inset',
        )}
      >
        Error Details
      </summary>
      <pre className="p-2 whitespace-pre-wrap break-words">{details}</pre>
    </details>
  );
}

/**
 * Prepare a URL that will pre-fill a support form with certain details
 * about the current error.
 */
function supportURL(errorMessage: string, error: ErrorLike): string {
  const supportURL = new URL('https://web.hypothes.is/get-help/');

  supportURL.searchParams.append('product', 'LMS_app');
  supportURL.searchParams.append(
    'subject',
    errorMessage
      ? `(LMS Error) ${errorMessage}`
      : 'Error encountered in Hypothesis LMS Application',
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

export type ErrorDisplayProps = {
  children?: ComponentChildren;

  /**
   * A short message explaining the error and its human-facing relevance,
   * provided by this (front-end) app for context.
   */
  description?: string;

  /**
   * Error-like object containing further `details` or `message` about this
   * error state. The value of `details` and `message` may come from a server
   * response.
   */
  error: ErrorLike;
};

/**
 * Displays human-facing details of an error
 */
export default function ErrorDisplay({
  children,
  description = '',
  error,
}: ErrorDisplayProps) {
  const message = formatErrorMessage(error, /* prefix */ description);

  return (
    <Scroll
      classes={classnames(
        // FIXME This class can be removed once the Modal in LMSFilePicker
        // has been updated to latest frontend-shared components.
        // Now it is needed to overwrite a style set on the modal itself.
        '!mt-0',
      )}
    >
      <div className="pt-4 space-y-4">
        {message && <p data-testid="error-message">{toSentence(message)}</p>}

        {children}
        <p data-testid="error-links">
          If the problem persists, you can{' '}
          <Link
            href={supportURL(message, error)}
            target="_blank"
            underline="always"
          >
            open a support ticket
          </Link>{' '}
          or visit our{' '}
          <Link
            href="https://web.hypothes.is/help/"
            target="_blank"
            underline="always"
          >
            help documents
          </Link>
          .
        </p>
        <ErrorDetails error={error} />
      </div>
    </Scroll>
  );
}
