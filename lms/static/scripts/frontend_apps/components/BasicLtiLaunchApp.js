import classNames from 'classnames';
import { Fragment, createElement } from 'preact';

import {
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'preact/hooks';

import { ApiError, apiCall } from '../utils/api';
import { Config } from '../config';

import AuthWindow from '../utils/AuthWindow';
import Dialog from './Dialog';
import Button from './Button';
import ErrorDisplay from './ErrorDisplay';
import LMSGrader from './LMSGrader';
import Spinner from './Spinner';

/**
 * @typedef {import('../services/client-rpc').ClientRpc} ClientRpc
 */

/**
 * The categories of error that can happen when launching an assignment.
 *
 * These affect the message that is shown to users and the actions
 * offered to remedy the problem.
 *
 * @typedef {'error-fetching'|'error-authorizing'|'error-reporting-submission'|'error-fetching-canvas-file'|'canvas-file-not-found-in-course'} ErrorState
 */

/**
 * @typedef BasicLtiLaunchAppProps
 * @prop {ClientRpc} clientRpc - Service for communicating with Hypothesis client
 */

/**
 * Application displayed when an assignment is launched if the LMS backend
 * is unable to directly render the content in an iframe. This happens when
 * the content URL needs to be fetched from a remote source (eg. the LMS's
 * file storage) first, which may require authorization from the user.
 *
 * @param {BasicLtiLaunchAppProps} props
 */
export default function BasicLtiLaunchApp({ clientRpc }) {
  const {
    api: {
      authToken,
      // API callback to use to fetch the URL to show in the iframe. This is
      // needed if resolving the content URL involves potentially slow calls
      // to third party APIs (eg. the LMS's file storage).
      viaUrl: viaUrlApi,
      // Sync API callback and data to asynchronously load the section groups
      // to relay to the sidebar via RPC.
      sync: apiSync,
    },
    grading,
    // Content URL to show in the iframe.
    viaUrl,
    canvas,
  } = useContext(Config);

  // Indicates what the application was doing when the error indicated by
  // `error` occurred.
  const [errorState, setErrorState] = useState(
    /** @type {ErrorState|null} */ (null)
  );

  // The most recent error that occurred when launching the assignment.
  const [error, setError] = useState(/** @type {Error|null} */ (null));

  // When the app is initially displayed, it will use the Via URL if given
  // or invoke the API callback to fetch the URL otherwise.
  const [contentUrl, setContentUrl] = useState(viaUrl ? viaUrl : null);

  // Count of pending API requests which must complete before the assignment
  // content can be shown.
  const [fetchCount, setFetchCount] = useState(0);

  // The authorization URL associated with the most recent failed API call.
  const [authUrl, setAuthUrl] = useState(/** @type {string|null} */ (null));

  // `AuthWindow` instance, set only when waiting for the user to approve
  // the app's access to the user's files in the LMS.
  const authWindow = useRef(/** @type {AuthWindow|null} */ (null));

  // Show the assignment when the contentUrl has resolved and errorState
  // is falsely
  const showIframe = contentUrl && !errorState;

  const showSpinner = fetchCount > 0 && !errorState;

  const incFetchCount = () => {
    setFetchCount(count => count + 1);
  };

  const decFetchCount = () => {
    setFetchCount(count => count - 1);
  };

  /**
   * Helper to handle thrown errors from from API requests.
   *
   * @param {Error} e - Error object from request.
   * @param {ErrorState} state
   * @param {boolean} [retry=true] - Can the request be retried?
   * @param {string} [authUrl] -
   *   Authorization URL association with the API request
   */
  const handleError = (e, state, retry = true, authUrl) => {
    // Here we always set the authorization URL, but we could improve UX by
    // not setting it if the problem is not related to authorization (eg.
    // a network fetch error).
    setAuthUrl(authUrl || null);

    if (
      e instanceof ApiError &&
      e.errorCode === 'canvas_api_permission_error'
    ) {
      setError(e);
      setErrorState('error-fetching-canvas-file');
    } else if (
      e instanceof ApiError &&
      e.errorCode === 'canvas_file_not_found_in_course'
    ) {
      setError(e);
      setErrorState('canvas-file-not-found-in-course');
    } else if (e instanceof ApiError && !e.errorMessage && retry) {
      setErrorState('error-authorizing');
    } else {
      setError(e);
      setErrorState(state);
    }
  };

  /**
   * Fetch the list of groups to show in the client.
   *
   * On the initial launch fetching groups does not block display of the assignment,
   * so `updateFetchCount` should be false. After re-authorization we wait
   * for group fetching to complete before showing the content, so `updateFetchCount`
   * should be true.
   */
  const fetchGroups = useCallback(
    async (updateFetchCount = false) => {
      if (!apiSync) {
        return true;
      }
      let success;

      if (updateFetchCount) {
        incFetchCount();
      }

      try {
        const groups = await apiCall({
          authToken,
          path: apiSync.path,
          data: apiSync.data,
        });
        clientRpc.setGroups(groups);
        success = true;
      } catch (e) {
        handleError(e, 'error-fetching', true /* retry */, apiSync.authUrl);
        success = false;
      }

      if (updateFetchCount) {
        decFetchCount();
      }

      return success;
    },
    [apiSync, authToken, clientRpc]
  );

  /**
   * Fetch the URL of the content to display in the iframe if `viaUrlApi`
   * exists.
   *
   * This will typically be a PDF URL proxied through Via.
   */
  const fetchContentUrl = useCallback(async () => {
    if (!viaUrlApi) {
      // If no "callback" URL was supplied for the frontend to use to fetch
      // the URL, then the backend must have provided the Via URL in the
      // initial request, which we'll just use directly.
      return true;
    }
    let success;
    incFetchCount();
    try {
      const { via_url: contentUrl } = await apiCall({
        authToken: authToken,
        path: viaUrlApi.path,
      });
      setContentUrl(contentUrl);
      success = true;
    } catch (e) {
      handleError(e, 'error-fetching', true /* retry */, viaUrlApi.authUrl);
      success = false;
    }
    decFetchCount();
    return success;
  }, [authToken, viaUrlApi]);

  /**
   * Fetch the assignment content URL and groups when the app is initially displayed.
   */
  useEffect(() => {
    fetchContentUrl();
    fetchGroups();
  }, [fetchContentUrl, fetchGroups]);

  /**
   * Report a submission to the LMS, with the LMS-provided metadata needed for
   * later grading of the assignment.
   */
  const reportSubmission = useCallback(async () => {
    // If a teacher launches an assignment or the LMS does not support reporting
    // outcomes or grading is not enabled for the assignment, then no submission
    // URL will be available.
    if (!canvas.speedGrader || !canvas.speedGrader.submissionParams) {
      return;
    }

    // Don't report a submission until the URL has been successfully fetched.
    if (!contentUrl) {
      return;
    }
    try {
      await apiCall({
        authToken,
        path: '/api/lti/submissions',
        data: canvas.speedGrader.submissionParams,
      });
    } catch (e) {
      // If reporting the submission failed, replace the content with an error.
      // This avoids the student trying to complete the assignment without
      // knowing that there was a problem, and the teacher then not seeing a
      // submission.
      handleError(e, 'error-reporting-submission', false);
    }
  }, [authToken, canvas.speedGrader, contentUrl]);

  useEffect(() => {
    reportSubmission();
  }, [reportSubmission]);

  /**
   * Request the user's authorization to access the content, then try fetching
   * the content URL and groups again.
   */
  const authorizeAndFetchUrl = useCallback(async () => {
    setErrorState('error-authorizing');

    if (authWindow.current) {
      authWindow.current.focus();
      return;
    }

    try {
      if (authUrl) {
        authWindow.current = new AuthWindow({ authToken, authUrl });
        await authWindow.current.authorize();
        setAuthUrl(null);
      }
      const [fetchedContent, fetchedGroups] = await Promise.all([
        fetchContentUrl(),
        fetchGroups(true /* updateFetchCount */),
      ]);
      if (fetchedContent && fetchedGroups) {
        setErrorState(null);
      }
    } finally {
      // @ts-ignore - The `current` field is incorrectly marked as not-nullable.
      authWindow.current = null;
    }
  }, [authToken, authUrl, fetchContentUrl, fetchGroups]);

  const refetchContentUrl = useCallback(async () => {
    const success = fetchContentUrl();
    if (success) {
      setErrorState(null);
    }
  }, [fetchContentUrl]);

  // Construct the <iframe> content
  let iFrameWrapper;
  const iFrame = (
    <iframe
      className="BasicLtiLaunchApp__iframe"
      src={contentUrl || ''}
      title="Course content with Hypothesis annotation viewer"
    />
  );

  if (grading && grading.enabled) {
    // Use the LMS Grader
    iFrameWrapper = (
      <LMSGrader
        clientRpc={clientRpc}
        students={grading.students}
        courseName={grading.courseName}
        assignmentName={grading.assignmentName}
      >
        {iFrame}
      </LMSGrader>
    );
  } else {
    // Use speed grader
    iFrameWrapper = iFrame;
  }

  const content = (
    <div
      // Visually hide the iframe / grader if there is an error or no contentUrl.
      className={classNames('BasicLtiLaunchApp__content', {
        'is-hidden': !showIframe,
      })}
    >
      {iFrameWrapper}
    </div>
  );

  const focusedDialogButton = useRef(
    /** @type {HTMLButtonElement | null} */ (null)
  );

  const errorDialog = (
    <Fragment>
      {errorState === 'error-authorizing' && (
        <Dialog
          initialFocus={focusedDialogButton}
          title="Authorize Hypothesis"
          role="alertdialog"
          buttons={[
            <Button
              disabled={fetchCount > 0}
              buttonRef={focusedDialogButton}
              onClick={authorizeAndFetchUrl}
              className="BasicLtiLaunchApp__button"
              label="Authorize"
              key="authorize"
            />,
          ]}
        >
          <p>Hypothesis needs your authorization to launch this assignment.</p>
        </Dialog>
      )}
      {errorState === 'error-fetching-canvas-file' && (
        <Dialog
          initialFocus={focusedDialogButton}
          title="Couldn't get the file from Canvas"
          role="alertdialog"
          buttons={[
            <Button
              buttonRef={focusedDialogButton}
              className="BasicLtiLaunchApp__button"
              disabled={fetchCount > 0}
              key="retry"
              label="Try again"
              onClick={refetchContentUrl}
            />,
          ]}
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
          <ErrorDisplay error={/** @type {Error} */ (error)} />
        </Dialog>
      )}
      {errorState === 'canvas-file-not-found-in-course' && (
        <Dialog
          initialFocus={focusedDialogButton}
          title="Hypothesis couldn't find the file in the course"
          role="alertdialog"
          buttons={[
            <Button
              buttonRef={focusedDialogButton}
              className="BasicLtiLaunchApp__button"
              disabled={fetchCount > 0}
              key="retry"
              label="Try again"
              onClick={refetchContentUrl}
            />,
          ]}
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

          <ErrorDisplay error={/** @type {Error} */ (error)} />
        </Dialog>
      )}
      {errorState === 'error-fetching' && (
        <Dialog
          initialFocus={focusedDialogButton}
          title="Something went wrong"
          contentClass="BasicLtiLaunchApp__dialog"
          role="alertdialog"
          buttons={[
            <Button
              disabled={fetchCount > 0}
              buttonRef={focusedDialogButton}
              onClick={authorizeAndFetchUrl}
              className="BasicLtiLaunchApp__button"
              label="Try again"
              key="retry"
            />,
          ]}
        >
          <ErrorDisplay
            message="There was a problem fetching this Hypothesis assignment"
            error={/** @type {Error} */ (error)}
          />
        </Dialog>
      )}
      {errorState === 'error-reporting-submission' && (
        <Dialog
          title="Something went wrong"
          contentClass="BasicLtiLaunchApp__dialog"
          role="alertdialog"
        >
          <ErrorDisplay
            message="There was a problem submitting this Hypothesis assignment"
            error={/** @type {Error} */ (error)}
          />
          <b>To fix this problem, try reloading the page.</b>
        </Dialog>
      )}
    </Fragment>
  );

  return (
    <div className="BasicLtiLaunchApp">
      {showSpinner && <Spinner className="BasicLtiLaunchApp__spinner" />}
      {errorDialog}
      {content}
    </div>
  );
}
