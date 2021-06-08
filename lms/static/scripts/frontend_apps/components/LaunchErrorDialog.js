import { LabeledButton } from '@hypothesis/frontend-shared';
import { createElement } from 'preact';
import { useRef } from 'preact/hooks';

import Dialog from './Dialog';
import ErrorDisplay from './ErrorDisplay';

/**
 * @typedef {import("preact").ComponentChildren} Children
 * @typedef {import('./BasicLtiLaunchApp').ErrorState} ErrorState
 */

/**
 * Common structure for LTI launch error dialogs.
 *
 * This is a "full-screen", non-cancelable dialog consisting of:
 *
 *  - An explanation of what went wrong and how to resolve it
 *  - An optional "Try again" button
 *  - An optional detailed error message for use when contacting support
 *
 * @param {Object} props
 * @param {boolean} props.busy
 * @param {Children} props.children
 * @param {Error|null} [props.error]
 * @param {() => void} [props.onRetry]
 * @param {string} [props.retryLabel]
 * @param {string} [props.title]
 */
function BaseDialog({
  busy,
  children,
  error = null,
  onRetry,
  retryLabel = 'Try again',
  title = 'Something went wrong',
}) {
  const focusedDialogButton = useRef(
    /** @type {HTMLButtonElement | null} */ (null)
  );
  return (
    <Dialog
      initialFocus={focusedDialogButton}
      title={title}
      role="alertdialog"
      buttons={
        onRetry && (
          <LabeledButton
            buttonRef={focusedDialogButton}
            disabled={busy}
            onClick={onRetry}
            variant="primary"
          >
            {retryLabel}
          </LabeledButton>
        )
      }
    >
      {children}
      {error && <ErrorDisplay error={error} />}
    </Dialog>
  );
}

/**
 * @typedef LaunchErrorDialogProps
 * @prop {boolean} busy -
 *   Flag indicating that the app is busy and should not allow the user to
 *   click the "Try again" button
 * @prop {ErrorState} errorState - What kind of error occurred?
 * @prop {Error|null} error - Detailed information about the error
 * @prop {() => void} onRetry -
 *   Callback invoked when user clicks the "Try again" button
 */

/**
 * Dialog that is displayed if an LTI launch failed.
 *
 * The dialog provides an explanation of what went wrong and steps to fix the
 * problem.
 *
 * @param {LaunchErrorDialogProps} props
 */
export default function LaunchErrorDialog({
  busy,
  error,
  errorState,
  onRetry,
}) {
  switch (errorState) {
    case 'error-authorizing':
      // nb. There are no error details shown here, since failing to authorize
      // is a "normal" event which will happen if the user has not authorized before
      // or the authorization has expired or been revoked.
      return (
        <BaseDialog
          busy={busy}
          onRetry={onRetry}
          retryLabel="Authorize"
          title="Authorize Hypothesis"
        >
          <p>Hypothesis needs your authorization to launch this assignment.</p>
        </BaseDialog>
      );
    case 'error-fetching-canvas-file':
      return (
        <BaseDialog
          busy={busy}
          error={error}
          onRetry={onRetry}
          title="Couldn't get the file from Canvas"
        >
          <p>
            Hypothesis couldn&apos;t get the assignment&apos;s file from Canvas.
          </p>
          <p>
            You might not have permission to read the file in Canvas. This could
            be because:
          </p>
          <ul>
            <li>
              The file is marked as <i>Unpublished</i> in Canvas: an instructor
              needs to publish the file.
            </li>
            <li>
              This course was copied from another course: an instructor needs to
              edit this assignment and re-select the file.
            </li>
          </ul>
        </BaseDialog>
      );
    case 'canvas-file-not-found-in-course':
      return (
        <BaseDialog
          busy={busy}
          error={error}
          onRetry={onRetry}
          title="Hypothesis couldn't find the file in the course"
        >
          <p>This might have happened because:</p>

          <ul>
            <li>The file has been deleted from Canvas</li>
            <li>The course was copied from another course</li>
          </ul>

          <p>
            To fix the issue,{' '}
            <a
              target="_blank"
              rel="noreferrer"
              href="https://web.hypothes.is/help/fixing-a-broken-canvas-file-link/"
            >
              edit the assignment and re-select the file
            </a>
            .
          </p>
        </BaseDialog>
      );

    case 'canvas-group-set-not-found':
      // nb. There is no retry action here as we just suggest reloading the entire
      // page.
      return (
        <BaseDialog busy={busy} error={error}>
          <p>
            There was a problem loading the group set for this Hypothesis
            assignment.{' '}
            <b>
              To fix this problem, double check the group set linked to this
              assigment still exists.
            </b>
          </p>
        </BaseDialog>
      );

    case 'error-fetching':
      return (
        <BaseDialog busy={busy} error={error} onRetry={onRetry}>
          <p>There was a problem fetching this Hypothesis assignment.</p>
        </BaseDialog>
      );
    case 'error-reporting-submission':
      // nb. There is no retry action here as we just suggest reloading the entire
      // page.
      return (
        <BaseDialog busy={busy} error={error}>
          <p>
            There was a problem submitting this Hypothesis assignment.{' '}
            <b>To fix this problem, try reloading the page.</b>
          </p>
        </BaseDialog>
      );
  }
}
