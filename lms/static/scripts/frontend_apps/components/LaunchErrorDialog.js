import { Link } from '@hypothesis/frontend-shared';

import ErrorModal from './ErrorModal';

/**
 * @typedef {import("preact").ComponentChildren} Children
 * @typedef {import('./BasicLTILaunchApp').ErrorState} ErrorState
 * @typedef {import('../errors').ErrorLike} ErrorLike
 */

/**
 * @typedef LaunchErrorDialogProps
 * @prop {boolean} busy -
 *   Flag indicating that the app is busy and should not allow the user to
 *   click the "Try again" button
 * @prop {ErrorState} errorState - What kind of error occurred?
 * @prop {ErrorLike|null} error - Detailed information about the error
 * @prop {() => void} onRetry -
 *   Callback invoked when user clicks the "Try again" button
 */

/**
 * Render an error that prevents an LTI launch from completing successfully.
 *
 * This is rendered in a non-cancelable modal.
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
      // or the authorization has expired or been revoked. This is handled
      // specially here by not passing the `error` on to `BaseDialog`
      return (
        <ErrorModal
          busy={busy}
          onRetry={onRetry}
          retryLabel="Authorize"
          title="Authorize Hypothesis"
        >
          <p>Hypothesis needs your authorization to launch this assignment.</p>
        </ErrorModal>
      );
    case 'blackboard_file_not_found_in_course':
      return (
        <ErrorModal
          busy={busy}
          error={error}
          onRetry={onRetry}
          title="Hypothesis couldn't find the file in the course"
        >
          <p>This might have happened because:</p>

          <ul className="u-list">
            <li>
              The file has been deleted from Blackboard: an instructor needs to
              re-create the assignment with a new file
            </li>
            <li>
              You don{"'"}t have permission to read the file: an instructor
              needs to{' '}
              <Link
                rel="noreferrer"
                href="https://web.hypothes.is/help/creating-hypothesis-enabled-readings-in-blackboard/"
              >
                give students read permission for the file
              </Link>
            </li>
          </ul>
        </ErrorModal>
      );
    case 'canvas_api_permission_error':
      return (
        <ErrorModal
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
          <ul className="u-list">
            <li>
              The file is marked as <i>Unpublished</i> in Canvas: an instructor
              needs to publish the file.
            </li>
            <li>
              This course was copied from another course: an instructor needs to
              edit this assignment and re-select the file.
            </li>
          </ul>
        </ErrorModal>
      );
    case 'canvas_file_not_found_in_course':
      return (
        <ErrorModal
          busy={busy}
          error={error}
          onRetry={onRetry}
          title="Hypothesis couldn't find the file in the course"
        >
          <p>This might have happened because:</p>

          <ul className="u-list">
            <li>The file has been deleted from Canvas</li>
            <li>The course was copied from another course</li>
          </ul>

          <p>
            To fix the issue,{' '}
            <Link
              target="_blank"
              href="https://web.hypothes.is/help/fixing-a-broken-canvas-file-link/"
            >
              edit the assignment and re-select the file
            </Link>
            .
          </p>
        </ErrorModal>
      );

    case 'blackboard_group_set_not_found':
    case 'canvas_group_set_not_found':
      return (
        <ErrorModal
          busy={busy}
          error={error}
          title="Assignment's group set no longer exists"
        >
          <p>
            Hypothesis couldn&apos;t load this assignment because the
            assignment&apos;s group set no longer exists.
          </p>
          <p>
            <b>
              To fix this problem, an instructor needs to edit the assignment
              settings and select a new group set.
            </b>
          </p>
        </ErrorModal>
      );

    case 'blackboard_group_set_empty':
    case 'canvas_group_set_empty':
      return (
        <ErrorModal
          busy={busy}
          error={error}
          title="Assignment's group set is empty"
        >
          <p>The group set for this Hypothesis assignment is empty. </p>
          <p>
            <b>
              To fix this problem, add groups to the group set or use a
              different group set for this assignment.
            </b>
          </p>
        </ErrorModal>
      );

    case 'blackboard_student_not_in_group':
      return (
        <ErrorModal
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
              To fix the problem, an instructor needs to add your Blackboard
              user account to one of this assignment&apos;s groups.
            </b>
          </p>
        </ErrorModal>
      );

    case 'canvas_student_not_in_group':
      return (
        <ErrorModal
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
        </ErrorModal>
      );

    case 'error-fetching':
      // Do not display canned text if there is a back-end-provided message
      // to show here, as it's redundant and not useful
      return (
        <ErrorModal
          busy={busy}
          error={error}
          onRetry={onRetry}
          title="Something went wrong"
        >
          {!error?.serverMessage && (
            <p>There was a problem fetching this Hypothesis assignment.</p>
          )}
        </ErrorModal>
      );
    case 'error-reporting-submission':
      // nb. There is no retry action here as we just suggest reloading the entire
      // page.
      return (
        <ErrorModal busy={busy} error={error} title="Something went wrong">
          <p>
            There was a problem submitting this Hypothesis assignment.{' '}
            <b>To fix this problem, try reloading the page.</b>
          </p>
        </ErrorModal>
      );
  }
}
