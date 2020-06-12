import classNames from 'classnames';
import { Fragment, createElement } from 'preact';
import propTypes from 'prop-types';

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
 * @typedef {Object} User
 * @property {string} userid - Unique user's id
 * @property {string} displayName - User's display name
 */

/**
 * Application displayed when an assignment is launched if the LMS backend
 * is unable to directly render the content in an iframe. This happens when
 * the content URL needs to be fetched from a remote source (eg. the LMS's
 * file storage) first, which may require authorization from the user.
 */
export default function BasicLtiLaunchApp({ rpcServer }) {
  const {
    api: {
      authToken,
      // API callback to use to fetch the URL to show in the iframe. This is
      // needed if resolving the content URL involves potentially slow calls
      // to third party APIs (eg. the LMS's file storage).
      viaCallbackUrl,
      // Sync API callback and data to asynchronously load the section groups
      // to relay to the sidebar via RPC.
      sync: apiSync,
    },
    grading,
    // Content URL to show in the iframe.
    viaUrl,
    canvas,
  } = useContext(Config);

  // The current state of the error.
  // One of "error-fetch", "error-authorizing", or "error-report-submission" or null
  const [errorState, setErrorState] = useState(null);

  // Any current error thrown.
  const [error, setError] = useState(null);

  // When the app is initially displayed, it will use the Via URL if given
  // or invoke the API callback to fetch the URL otherwise.
  const [contentUrl, setContentUrl] = useState(viaUrl ? viaUrl : null);

  // How many current blocking request are pending
  const [fetchCount, setFetchCount] = useState(0);

  // `AuthWindow` instance, set only when waiting for the user to approve
  // the app's access to the user's files in the LMS.
  const authWindow = useRef(null);

  // Helpers
  const hasError = !!errorState;

  // Show the assignment when the contentUrl has resolved and errorState
  // is falsely
  const showIframe = contentUrl && !hasError;

  const showPageSpinner = fetchCount > 0 && !hasError;
  const showDialogSpinner = fetchCount > 0 && hasError;

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
   * @param {string} newErrorState - One of "error-fetch",
   *  "error-authorizing", or "error-report-submission"
   * @param {boolean} [retry=true] - Can the request be retried?
   */
  const handleError = useCallback((e, newErrorState, retry = true) => {
    if (e instanceof ApiError && !e.errorMessage && retry) {
      setErrorState('error-authorizing');
    } else {
      setError(e);
      setErrorState(newErrorState);
    }
  }, []);

  /**
   * Fetch the groups from the sync endpoint if `sync` object exists.
   *
   * @returns {number} - 1 if an error occurred, 0 otherwise
   */
  const fetchGroups = useCallback(async () => {
    if (apiSync) {
      try {
        const groups = await apiCall({
          authToken,
          path: apiSync.path,
          data: apiSync.data,
        });
        rpcServer.resolveGroupFetch(groups);
        return 0;
      } catch (e) {
        handleError(e, 'error-fetch');
        return 1;
      }
    }
    return 0;
  }, [apiSync, authToken, handleError, rpcServer]);

  /**
   * Fetch the URL of the content to display in the iframe if `viaCallbackUrl`
   * exists.
   *
   * This will typically be a PDF URL proxied through Via.
   *
   * @returns {number} - 1 if an error occurred, 0 otherwise
   */
  const fetchContentUrl = useCallback(async () => {
    if (!viaCallbackUrl) {
      // If no "callback" URL was supplied for the frontend to use to fetch
      // the URL, then the backend must have provided the Via URL in the
      // initial request, which we'll just use directly.

      return 0;
    }
    try {
      incFetchCount();
      const { via_url: contentUrl } = await apiCall({
        authToken: authToken,
        path: viaCallbackUrl,
      });
      setContentUrl(contentUrl);
      decFetchCount();
      return 0;
    } catch (e) {
      decFetchCount();
      handleError(e, 'error-fetch');
      return 1; // error state
    }
  }, [authToken, handleError, viaCallbackUrl]);

  /**
   * Fetch the assignment content URL and groups when the app is initially displayed.
   */
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(async () => {
    fetchGroups();
    fetchContentUrl();
  }, [fetchContentUrl, fetchGroups]);

  /**
   * Report a submission to the LMS, with the LMS-provided metadata needed for
   * later grading of the assignment.
   */
  const reportSubmission = async () => {
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
      handleError(e, 'error-report-submission', false);
    }
  };

  useEffect(reportSubmission, [authToken, canvas.speedGrader, contentUrl]);

  /**
   * Request the user's authorization to access the content, then try fetching
   * the content URL and groups again.
   */

  const authorizeAndFetchUrl = useCallback(async () => {
    if (authWindow.current) {
      authWindow.current.focus();
      return;
    }
    authWindow.current = new AuthWindow({ authToken, authUrl: canvas.authUrl });
    try {
      await authWindow.current.authorize();

      // In the re-try case, block only the contentUrl request. At
      // the time is succeeds, check the error code groups too. There
      // are two possible cases:
      //
      // 1. Groups did finish.
      //   If the groups request errors, then don't reset
      //   the the errorState as that may cause a flickering.
      //
      // 2. Groups did not finish.
      //   Just allow the group to finish on its own and it will
      //   take care of setting any new error, We can't prevent
      //   the UI from jumping around at that point because we
      //   don't block on the groups request in the first place.
      let groupError = 0;
      fetchGroups().then(error => {
        // This may or may not resolve before fetchContentUrl.
        // We only care if it resolves first AND if an error code
        // was returned
        groupError = error;
      });
      if (!(await fetchContentUrl())) {
        // Clear out an old error if no new error occurs.
        if (!groupError) {
          // Okay to clear the error state
          setErrorState(null);
        }
      }
    } finally {
      authWindow.current = null;
    }
  }, [authToken, canvas.authUrl, fetchContentUrl, fetchGroups]);

  // Construct the <iframe> content
  let iFrameWrapper;
  const iFrame = (
    <iframe
      width="100%"
      height="100%"
      className="js-via-iframe"
      src={contentUrl}
      title="Course content with Hypothesis annotation viewer"
    />
  );

  if (grading && grading.enabled) {
    // Use the LMS Grader
    iFrameWrapper = (
      <LMSGrader
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
    <span
      // Visually hide the iframe / grader if there is an error or no contentUrl.
      className={classNames('BasicLtiLaunchApp__content', {
        'is-hidden': !showIframe,
      })}
    >
      {iFrameWrapper}
    </span>
  );

  const errorDialog = (
    <Fragment>
      {errorState === 'error-authorizing' && (
        <Dialog
          title="Authorize Hypothesis"
          role="alertdialog"
          isLoading={showDialogSpinner}
          buttons={[
            <Button
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
      {errorState === 'error-fetch' && (
        <Dialog
          title="Something went wrong"
          contentClass="BasicLtiLaunchApp__dialog"
          role="alertdialog"
          isLoading={showDialogSpinner}
          buttons={[
            <Button
              onClick={authorizeAndFetchUrl}
              className="BasicLtiLaunchApp__button"
              label="Try again"
              key="retry"
            />,
          ]}
        >
          <ErrorDisplay
            message="There was a problem fetching this Hypothesis assignment"
            error={error}
          />
        </Dialog>
      )}
      {errorState === 'error-report-submission' && (
        <Dialog
          title="Something went wrong"
          contentClass="BasicLtiLaunchApp__dialog"
          role="alertdialog"
        >
          <ErrorDisplay
            message="There was a problem submitting this Hypothesis assignment"
            error={error}
          />
          <b>To fix this problem, try reloading the page.</b>
        </Dialog>
      )}
    </Fragment>
  );

  return (
    <span className="BasicLtiLaunchApp">
      <Spinner
        visible={showPageSpinner}
        className="BasicLtiLaunchApp__spinner"
      />
      {errorDialog}
      {content}
    </span>
  );
}

BasicLtiLaunchApp.propTypes = {
  rpcServer: propTypes.object.isRequired,
};
