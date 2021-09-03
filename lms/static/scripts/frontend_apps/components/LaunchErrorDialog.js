import { LabeledButton } from '@hypothesis/frontend-shared';

import { useRef } from 'preact/hooks';

import Dialog from './Dialog';
import ErrorDisplay from './ErrorDisplay';

/**
 * @typedef {import("preact").ComponentChildren} Children
 * @typedef {import('./BasicLTILaunchApp').ErrorState} ErrorState
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
    case 'blackboard_file_not_found_in_course':
      return (
        <BaseDialog
          busy={busy}
          error={error}
          onRetry={onRetry}
          title="Hypothesis couldn't find the file in the course"
        >
          <p>This might have happened because:</p>

          <ul>
            <li>
              The file has been deleted from Blackboard: an instructor needs to
              re-create the assignment with a new file
            </li>
            <li>
              You don{"'"}t have permission to read the file: an instructor
              needs to{' '}
              <a
                target="_blank"
                rel="noreferrer"
                href="https://web.hypothes.is/help/creating-hypothesis-enabled-readings-in-blackboard/"
              >
                give students read permission for the file
              </a>
            </li>
          </ul>
        </BaseDialog>
      );
    case 'canvas_api_permission_error':
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
    case 'canvas_file_not_found_in_course':
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

    case 'canvas_group_set_not_found':
      return (
        <BaseDialog
          busy={busy}
          error={error}
          title="Assignment's group set no longer exists in Canvas"
        >
          <p>
            Hypothesis couldn&apos;t load this assignment because the
            assignment&apos;s group set no longer exists in Canvas.
          </p>
          <p>
            <b>
              To fix this problem, an instructor needs to edit the assignment
              settings and select a new group set.
            </b>
          </p>
        </BaseDialog>
      );

    case 'canvas_group_set_empty':
      return (
        <BaseDialog busy={busy} error={error}>
          <p>The group set for this Hypothesis assignment is empty. </p>
          <p>
            <b>
              To fix this problem, add groups to the group set or use a
              different group set for this assignment.
            </b>
          </p>
        </BaseDialog>
      );

    case 'canvas_student_not_in_group':
      return (
        <BaseDialog
          busy={busy}
          error={error}
          title="You're not in any of this assignment's groups"
        >
          <p>
            Hypothesis couldn&apos;t launch this assignment because you
            aren&apos;t in any of the groups in the assignment&apos;s group set.
          </p>
          <p>
            <b>
              To fix the problem, an instructor needs to add your Canvas user
              account to one of this assignment&apos;s groups.
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
