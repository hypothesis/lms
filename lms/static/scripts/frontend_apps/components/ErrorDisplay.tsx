import { Link, Scroll } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { ComponentChildren } from 'preact';

import { useConfig, type DebugInfo } from '../config';
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
function supportURL(
  errorMessage: string,
  error: ErrorLike,
  debug?: DebugInfo,
): string {
  const supportURL = new URL('https://web.hypothes.is/get-help/');

  supportURL.searchParams.append('product', 'LMS_app');
  supportURL.searchParams.append(
    'subject',
    errorMessage
      ? `(LMS Error) ${errorMessage}`
      : 'Error encountered in Hypothesis LMS Application',
  );

  const details = formatErrorDetails(error);
  if (error.errorCode || details || debug) {
    const content = `
----------------------
Feel free to add additional details above about the problem you are experiencing.
The error information below helps our team pinpoint the issue faster.
----------------------
Error code: ${error.errorCode ?? 'N/A'}
Details: ${formatErrorDetails(error) || 'N/A'}
Debug: ${(debug && JSON.stringify(debug)) || 'N/A'}
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

  /**
   * Wether or not to show the standard link to our support page
   */
  displaySupportLink?: boolean;

  /** Extra CSS classes to append to the error display wrapper */
  classes?: string | string[];
};

/**
 * Displays human-facing details of an error
 */
export default function ErrorDisplay({
  children,
  description = '',
  error,
  displaySupportLink = true,
  classes,
}: ErrorDisplayProps) {
  const message = formatErrorMessage(error, /* prefix */ description);

  const { debug } = useConfig();

  return (
    <Scroll classes={classes}>
      <div className="space-y-4">
        {message && <p data-testid="error-message">{toSentence(message)}</p>}

        {children}
        {displaySupportLink && (
          <p data-testid="error-links">
            If the problem persists, you can{' '}
            <Link
              href={supportURL(message, error, debug)}
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
        )}

        <ErrorDetails error={error} />
      </div>
    </Scroll>
  );
}
