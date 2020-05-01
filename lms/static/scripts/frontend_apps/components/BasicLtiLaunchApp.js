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
      sync: apiSync,
    },
    grading,
    // Content URL to show in the iframe.
    viaUrl,
    canvas,
  } = useContext(Config);

  // The current state of the error.
  // One "error-fetch", "error-authorizing"
  const [errorState, setErrorState] = useState(null);

  // Any current error message to render to a dialog
  const [errorMessage, setErrorMessage] = useState(null);

  // When the app is initially displayed it will use the Via URL if given
  // or invoke the API callback to fetch the URL otherwise.
  const [contentUrl, setContentUrl] = useState(viaUrl ? viaUrl : null);

  // How many current request are pending
  const [fetchCount, setFetchCount] = useState(0);

  // Non-rendered var to keep track of the fetchCount
  const count = useRef(0);

  // `AuthWindow` instance, set only when waiting for the user to approve
  // the app's access to the user's files in the LMS.
  const authWindow = useRef(null);

  // Show the assignment when there are no pending requests
  // and no errorState
  const showIframe = () => {
    return fetchCount === 0 && !errorState;
  };

  // Show the loader is there are any pending requests and
  // no errorState
  const showSpinner = () => {
    return !errorState && fetchCount > 0;
  };

  // Increment the fetch counter by 1 and clear any
  // previous error state.
  const setFetching = () => {
    count.current += 1;
    setFetchCount(count.current);
    setErrorState(null);
  };

  // Decrement the fetch counter by 1.
  const setFetched = () => {
    count.current -= 1;
    setFetchCount(count.current);
  };

  // Helper to handle error events from api requests
  const handleError = async (e, errorState) => {
    setFetched();
    if (e instanceof ApiError && !e.errorMessage) {
      setErrorState('error-authorizing');
    } else {
      setErrorMessage(e.errorMessage);
      setErrorState(errorState);
    }
  };

  /**
   * Fetch the groups from the sync endpoint
   */
  const fetchGroups = async () => {
    if (apiSync) {
      try {
        setFetching();
        const groups = await apiCall({
          authToken,
          path: apiSync.path,
          data: apiSync.data,
        });
        rpcServer.resolveGroupFetch(groups);
        setFetched();
      } catch (e) {
        handleError(e, 'error-fetch');
      }
    }
  };

  /**
   * Fetch the URL of the content to display in the iframe.
   *
   * This will typically be a PDF URL proxied through Via.
   */
  const fetchContentUrl = async () => {
    if (!viaCallbackUrl) {
      // If no "callback" URL was supplied for the frontend to use to fetch
      // the URL, then the backend must have provided the Via URL in the
      // initial request, which we'll just use directly.
      return;
    }
    try {
      setFetching();
      const { via_url: contentUrl } = await apiCall({
        authToken,
        path: viaCallbackUrl,
      });
      setFetched();
      setContentUrl(contentUrl);
    } catch (e) {
      handleError(e, 'error-fetch');
    }
  };

  /**
   * Fetch the assignment content URL and groups when the app is initially displayed.
   */
  useEffect(() => {
    fetchContentUrl();
    fetchGroups();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
      handleError(e, 'error-report-submission');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authToken, canvas.speedGrader, contentUrl]);

  useEffect(reportSubmission, [reportSubmission]);

  /**
   * Request the user's authorization to access the content, then try fetching
   * the content URL again.
   */
  const authorizeAndFetchUrl = useCallback(async () => {
    setErrorState('error-authorizing');

    if (authWindow.current) {
      authWindow.current.focus();
      return;
    }
    authWindow.current = new AuthWindow({ authToken, authUrl: canvas.authUrl });

    try {
      await authWindow.current.authorize();
      await Promise.all([fetchContentUrl(authToken), fetchGroups(authToken)]);
    } finally {
      authWindow.current = null;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [authToken, canvas.authUrl]);

  if (showIframe()) {
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
      // Use the LMS Grader.
      return (
        <LMSGrader
          students={grading.students}
          courseName={grading.courseName}
          assignmentName={grading.assignmentName}
        >
          {iFrame}
        </LMSGrader>
      );
    } else {
      return iFrame;
    }
  } else {
    // Render either a Spinner or Dialog.
    return (
      <Fragment>
        {showSpinner() && <Spinner className="BasicLtiLaunchApp__spinner" />}
        {errorState === 'error-authorizing' && (
          <Dialog
            title="Authorize Hypothesis"
            role="alertdialog"
            buttons={[
              <Button
                onClick={authorizeAndFetchUrl}
                className="BasicLtiLaunchApp__button"
                label="Authorize"
                key="authorize"
              />,
            ]}
          >
            <p>
              Hypothesis needs your authorization to launch this assignment.
            </p>
          </Dialog>
        )}
        {errorState === 'error-fetch' && (
          <Dialog
            title="Something went wrong"
            contentClass="BasicLtiLaunchApp__dialog"
            role="alertdialog"
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
              error={errorMessage}
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
              error={errorMessage}
            />
            <b>To fix this problem, try reloading the page.</b>
          </Dialog>
        )}
      </Fragment>
    );
  }
}

BasicLtiLaunchApp.propTypes = {
  rpcServer: propTypes.object,
};
