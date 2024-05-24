import { Link } from '@hypothesis/frontend-shared';
import { Link as RouterLink } from 'wouter-preact';

import { useConfig } from '../config';
import type { ErrorLike } from '../errors';
import type { ErrorState } from './BasicLTILaunchApp';
import ErrorModal from './ErrorModal';

export type LaunchErrorDialogProps = {
  /**
   * Flag indicating that the app is busy and should not allow the user to
   * click the "Try again" button
   */
  busy: boolean;
  /** What kind of error occurred? */
  errorState: ErrorState;
  /** Detailed information about the error */
  error: ErrorLike | null;
  /** Callback invoked when user clicks the "Try again" button */
  onRetry: () => void;
};

/**
 * URL that opens the VitalSource bookshelf reader in the current LMS.
 *
 * TODO: This should be replaced with an installation-specific link that opens
 * VitalSource inside the current LMS. This allows an association between the
 * LTI user and VitalSource account to be established.
 */
const vitalsourceBookshelfURL = 'https://bookshelf.vitalsource.com';

/**
 * A link to a support page or other external resource within an error message.
 */
function ExternalLink({ children, href }: { children: string; href: string }) {
  // nb. Link is always underlined on the assumption it is appearing in the
  // middle of a paragraph.
  return (
    <Link target="_blank" href={href} underline="always">
      {children}
    </Link>
  );
}

/**
 * Link to a generic KB article for Moodle error codes.
 */
function MoodleKBLink() {
  return (
    <ExternalLink href="https://web.hypothes.is/help/troubleshooting-lms-app-error-messages-in-moodle/">
      Troubleshooting LMS App Error Messages in Moodle
    </ExternalLink>
  );
}

/**
 * Render an error that prevents an LTI launch from completing successfully.
 *
 * This is rendered in a non-cancelable modal.
 */
export default function LaunchErrorDialog({
  busy,
  error,
  errorState,
  onRetry,
}: LaunchErrorDialogProps) {
  const { instructorToolbar } = useConfig();
  const canEdit = Boolean(instructorToolbar?.editingEnabled);

  let extraActions;
  if (canEdit) {
    extraActions = (
      <RouterLink href="/app/content-item-selection" asChild>
        <Link underline="always" data-testid="edit-link">
          Edit assignment
        </Link>
      </RouterLink>
    );
  }

  // Common properties for error dialog.
  const defaultProps = {
    busy,
    extraActions,
    error,

    // FIXME: Retrying the launch is enabled by default, but many error cases
    // disable it. This feels a bit haphazard. Perhaps we can improve consistency
    // in future by always providing this option?
    onRetry,
  };

  switch (errorState) {
    case 'error-authorizing':
      // nb. There are no error details shown here, since failing to authorize
      // is a "normal" event which will happen if the user has not authorized before
      // or the authorization has expired or been revoked. This is handled
      // specially here by not passing the `error` on to `BaseDialog`
      return (
        <ErrorModal
          {...defaultProps}
          error={undefined}
          retryLabel="Authorize"
          title="Authorize Hypothesis"
        >
          <p>Hypothesis needs your authorization to launch this assignment.</p>
        </ErrorModal>
      );
    case 'blackboard_file_not_found_in_course':
      return (
        <ErrorModal
          {...defaultProps}
          title="Hypothesis couldn't find the file in the course"
        >
          <p>This might have happened because:</p>

          <ul className="px-4 list-disc">
            <li>
              The file has been deleted from Blackboard: an instructor needs to
              {canEdit ? 'edit' : 'recreate'} this assignment and select a new
              file
            </li>
            <li>
              You don{"'"}t have permission to read the file: an instructor
              needs to{' '}
              <ExternalLink href="https://web.hypothes.is/help/creating-hypothesis-enabled-readings-in-blackboard/">
                give students read permission for the file
              </ExternalLink>
            </li>
          </ul>
        </ErrorModal>
      );

    case 'd2l_file_not_found_in_course_instructor':
      return (
        <ErrorModal
          {...defaultProps}
          title="Hypothesis couldn't find the file in the course"
        >
          <p>This might have happened because:</p>
          <ul className="px-4 list-disc">
            <li>The file has been deleted from D2L</li>
            <li>
              The course was copied and the selected file is not available in
              the new course.
            </li>
          </ul>
          <p>
            To fix the issue, {canEdit ? 'edit' : 'recreate'} this assignment
            and select a different file. More information can be found in our
            document about{' '}
            <ExternalLink href="https://web.hypothes.is/help/using-hypothesis-with-d2l-course-content-files/">
              Using Hypothesis With D2L Course Content Files
            </ExternalLink>
            .
          </p>
        </ErrorModal>
      );

    case 'd2l_file_not_found_in_course_student':
      return (
        <ErrorModal
          {...defaultProps}
          title="Hypothesis couldn't find the file in the course"
        >
          <p>This might have happened because:</p>
          <ul className="px-4 list-disc">
            <li>The file has been deleted from D2L</li>
            <li>
              The course was copied and the selected file is not available in
              the new course.
            </li>
          </ul>
          <p>
            Please ask the course instructor to review the settings of this
            assignment.
          </p>
        </ErrorModal>
      );

    case 'moodle_file_not_found_in_course':
      return (
        <ErrorModal
          {...defaultProps}
          title="Hypothesis couldn't find the file in the course"
        >
          <p>This might have happened because:</p>
          <ul className="px-4 list-disc">
            <li>The file has been deleted from Moodle</li>
            <li>
              The course was copied and the selected file is not available in
              the new course.
            </li>
          </ul>
          <p>
            To fix the issue an instructor needs to edit this assignment and
            select a different file.
          </p>
          <p>
            <MoodleKBLink />
          </p>
        </ErrorModal>
      );

    case 'moodle_page_not_found_in_course':
      return (
        <ErrorModal
          {...defaultProps}
          title="Hypothesis couldn't find the page in the course"
        >
          <p>This might have happened because:</p>
          <ul className="px-4 list-disc">
            <li>The page has been deleted from Moodle</li>
            <li>The course was copied from another course</li>
          </ul>
          <p>
            <MoodleKBLink />
          </p>
        </ErrorModal>
      );

    case 'canvas_api_permission_error':
      return (
        <ErrorModal {...defaultProps} title="Couldn't get the file from Canvas">
          <p>
            Hypothesis couldn&apos;t get the assignment&apos;s file from Canvas.
          </p>
          <p>
            You might not have permission to read the file in Canvas. This could
            be because:
          </p>
          <ul className="px-4 list-disc">
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
          {...defaultProps}
          title="Hypothesis couldn't find the file in the course"
        >
          <p>This might have happened because:</p>

          <ul className="px-4 list-disc">
            <li>The file has been deleted from Canvas</li>
            <li>The course was copied from another course</li>
          </ul>

          <p>
            To fix the issue,{' '}
            <ExternalLink href="https://web.hypothes.is/help/fixing-a-broken-canvas-file-link/">
              edit the assignment and re-select the file
            </ExternalLink>
            .
          </p>
        </ErrorModal>
      );

    case 'canvas_page_not_found_in_course':
      return (
        <ErrorModal
          {...defaultProps}
          title="Hypothesis couldn't find the page in the course"
        >
          <p>This might have happened because:</p>

          <ul className="px-4 list-disc">
            <li>The page has been deleted from Canvas</li>
            <li>The course was copied from another course</li>
          </ul>
        </ErrorModal>
      );

    case 'canvas_group_set_not_found':
      return (
        <ErrorModal
          {...defaultProps}
          onRetry={undefined}
          title="Group set not found"
        >
          <p>
            This Hypothesis assignment was set up to use Canvas{"'"} Group Sets,
            and we can no longer find the Group Set for this assignment. This
            could be because:
          </p>

          <ul className="px-4 list-disc">
            <li>The group set has been deleted from Canvas.</li>
            <li>This course was created by copying another course.</li>
          </ul>
          <p>
            If the group set has been <b>deleted</b> from this course, an
            instructor needs to edit the assignment settings and select a group
            set.
          </p>

          <p>
            If this is a <b>copied course</b> the instructor needs to create a
            new group set in this course that matches the name of the group set
            in the old course.
          </p>
          {error?.details &&
            typeof error.details === 'object' &&
            'group_set_name' in error.details &&
            typeof error.details.group_set_name === 'string' && (
              <p>
                {' '}
                The group set name in the old course was:{' '}
                <b>{error.details.group_set_name}</b>
              </p>
            )}
        </ErrorModal>
      );

    case 'canvas_studio_download_unavailable':
      return (
        <ErrorModal
          {...defaultProps}
          onRetry={undefined}
          title="Unable to fetch Canvas Studio video"
        >
          <p>
            Only videos uploaded directly to Canvas Studio can be used. Videos
            hosted on YouTube or Vimeo cannot be used.
          </p>
        </ErrorModal>
      );

    case 'canvas_studio_media_not_found':
      return (
        <ErrorModal
          {...defaultProps}
          onRetry={undefined}
          title="Canvas Studio media not found"
        />
      );

    case 'canvas_studio_transcript_unavailable':
      return (
        <ErrorModal
          {...defaultProps}
          onRetry={undefined}
          title="Video does not have a published transcript"
        >
          <p>
            To use a video with Hypothesis, you must upload or generate captions
            in Canvas Studio <i>and</i> publish them.
          </p>
        </ErrorModal>
      );

    case 'canvas_studio_admin_token_refresh_failed':
      return (
        <ErrorModal
          {...defaultProps}
          onRetry={undefined}
          title="Unable to access Canvas Studio video"
        >
          <p>
            Your Canvas LMS administrator needs to re-authorize the integration
            between Hypothesis and Canvas Studio.
          </p>
        </ErrorModal>
      );

    case 'blackboard_group_set_not_found':
      return (
        <ErrorModal
          {...defaultProps}
          onRetry={undefined}
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
    case 'd2l_group_set_not_found':
      return (
        <ErrorModal
          {...defaultProps}
          onRetry={undefined}
          title="Assignment's group category no longer exists"
        >
          <p>
            Hypothesis couldn&apos;t load this assignment because the
            assignment&apos;s group category no longer exists.
          </p>
          <p>
            <b>
              To fix this problem, an instructor needs to edit the assignment
              settings and select a new group category.
            </b>
          </p>
        </ErrorModal>
      );

    case 'moodle_group_set_not_found':
      return (
        <ErrorModal
          {...defaultProps}
          onRetry={undefined}
          title="Assignment's grouping no longer exists"
        >
          <p>
            Hypothesis couldn&apos;t load this assignment because the
            assignment&apos;s grouping no longer exists.
          </p>
          <p>
            <b>
              To fix this problem, an instructor needs to edit the assignment
              settings and select a new grouping.
            </b>
          </p>
          <p>
            <MoodleKBLink />
          </p>
        </ErrorModal>
      );

    case 'blackboard_group_set_empty':
    case 'canvas_group_set_empty':
      return (
        <ErrorModal
          {...defaultProps}
          onRetry={undefined}
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
    case 'd2l_group_set_empty':
      return (
        <ErrorModal
          {...defaultProps}
          onRetry={undefined}
          title="Assignment's group category is empty"
        >
          <p>The group category for this Hypothesis assignment is empty. </p>
          <p>
            <b>
              To fix this problem, add groups to the group category or use a
              different group category for this assignment.
            </b>
          </p>
        </ErrorModal>
      );

    case 'moodle_group_set_empty':
      return (
        <ErrorModal
          {...defaultProps}
          onRetry={undefined}
          title="Assignment's grouping is empty"
        >
          <p>The grouping for this Hypothesis assignment is empty. </p>
          <p>
            <b>
              To fix this problem, add groups to the grouping or use a different
              grouping for this assignment.
            </b>
          </p>
          <p>
            <MoodleKBLink />
          </p>
        </ErrorModal>
      );

    case 'blackboard_student_not_in_group':
      return (
        <ErrorModal
          {...defaultProps}
          onRetry={undefined}
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
          {...defaultProps}
          onRetry={undefined}
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

    case 'd2l_student_not_in_group':
      return (
        <ErrorModal
          {...defaultProps}
          onRetry={undefined}
          title="You're not in any of this assignment's groups"
        >
          <p>
            Hypothesis couldn&apos;t launch this assignment because you
            aren&apos;t in any of the groups in the assignment&apos;s group
            category.
          </p>
          <p>
            <b>
              To fix the problem, an instructor needs to add your D2L user
              account to one of this assignment&apos;s groups.
            </b>
          </p>
        </ErrorModal>
      );

    case 'moodle_student_not_in_group':
      return (
        <ErrorModal
          {...defaultProps}
          onRetry={undefined}
          title="You're not in any of this assignment's groups"
        >
          <p>
            Hypothesis couldn&apos;t launch this assignment because you
            aren&apos;t in any of the groups in the assignment&apos;s grouping.
          </p>
          <p>
            <b>
              To fix the problem, an instructor needs to add your Moodle user
              account to one of this assignment&apos;s groupings.
            </b>
          </p>
          <p>
            <MoodleKBLink />
          </p>
        </ErrorModal>
      );

    case 'vitalsource_user_not_found':
      return (
        <ErrorModal
          {...defaultProps}
          onRetry={undefined}
          title="VitalSource account not found"
        >
          <p>Hypothesis could not find your VitalSource user account.</p>
          <p>
            This account is set up the first time that you open the VitalSource
            book reader.{' '}
            <b>
              To fix the problem, please open the{' '}
              <ExternalLink href={vitalsourceBookshelfURL}>
                VitalSource book reader
              </ExternalLink>
              .
            </b>
          </p>
        </ErrorModal>
      );

    case 'vitalsource_no_book_license':
      return (
        // TODO: Add some details of _which_ book is not available.
        <ErrorModal
          {...defaultProps}
          onRetry={undefined}
          title="Book not available"
        >
          <p>Your VitalSource library does not have this book in it.</p>
          <p>
            <b>
              To fix the problem, open the{' '}
              <ExternalLink href={vitalsourceBookshelfURL}>
                VitalSource book reader
              </ExternalLink>{' '}
              and add the book to your library.
            </b>
          </p>
        </ErrorModal>
      );

    case 'error-fetching':
      // Do not display canned text if there is a back-end-provided message
      // to show here, as it's redundant and not useful
      return (
        <ErrorModal {...defaultProps} title="Something went wrong">
          {!error?.serverMessage && (
            <p>There was a problem fetching this Hypothesis assignment.</p>
          )}
        </ErrorModal>
      );

    case 'error-reporting-submission':
      // nb. There is no retry action here as we just suggest reloading the entire
      // page.
      return (
        <ErrorModal
          {...defaultProps}
          onRetry={undefined}
          title="Something went wrong"
        >
          <p>
            There was a problem submitting this Hypothesis assignment.{' '}
            <b>To fix this problem, try reloading the page.</b>
          </p>
        </ErrorModal>
      );
  }
}
