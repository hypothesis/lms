import { Fragment, createElement } from 'preact';
import {
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'preact/hooks';

import AuthWindow from '../utils/AuthWindow';
import { Config } from '../config';
import { ApiError, apiCall } from '../utils/api';

import Button from './Button';
import ErrorDisplay from './ErrorDisplay';
import Spinner from './Spinner';

const INITIAL_LTI_LAUNCH_STATE = {
  // The current state of the screen.
  // One of "fetching", "fetched-url", "authorizing" or "error".
  //
  // When the app is initially displayed it will use the Via URL if given
  // or invoke the API callback to fetch the URL otherwise.
  state: 'fetching-url',

  // URL of assignment content. Set when state is "fetched-url".
  contentUrl: null,

  // Details of last error. Set when state is "error".
  error: null,

  // The action that resulted in an error.
  failedAction: null,
};

/**
 * Application displayed when an assignment is launched if the LMS backend
 * is unable to directly render the content in an iframe. This happens when
 * the content URL needs to be fetched from a remote source (eg. the LMS's
 * file storage) first, which may require authorization from the user.
 */
export default function BasicLtiLaunchApp() {
  const {
    authToken,
    authUrl,
    lmsName,
    submissionParams,
    urls: {
      // Content URL to show in the iframe.
      via_url: viaUrl,
      // API callback to use to fetch the URL to show in the iframe. This is
      // needed if resolving the content URL involves potentially slow calls
      // to third party APIs (eg. the LMS's file storage).
      via_url_callback: viaUrlCallback,
    },
  } = useContext(Config);

  const [ltiLaunchState, setLtiLaunchState] = useState({
    ...INITIAL_LTI_LAUNCH_STATE,
    state: viaUrlCallback ? 'fetching-url' : 'fetched-url',
    contentUrl: viaUrl ? viaUrl : null,
  });

  /**
   * Fetch the URL of the content to display in the iframe.
   *
   * This will typically be a PDF URL proxied through Via.
   */
  const fetchContentUrl = useCallback(async () => {
    if (!viaUrlCallback) {
      // If no "callback" URL was supplied for the frontend to use to fetch
      // the URL, then the backend must have provided the Via URL in the
      // initial request, which we'll just use directly.
      return;
    }

    try {
      setLtiLaunchState({
        ...INITIAL_LTI_LAUNCH_STATE,
        state: 'fetching-url',
      });
      const { via_url: contentUrl } = await apiCall({
        authToken,
        path: viaUrlCallback,
      });
      setLtiLaunchState({
        ...INITIAL_LTI_LAUNCH_STATE,
        state: 'fetched-url',
        contentUrl,
      });
    } catch (e) {
      if (e instanceof ApiError && !e.errorMessage) {
        setLtiLaunchState({
          ...INITIAL_LTI_LAUNCH_STATE,
          state: 'authorizing',
        });
      } else {
        setLtiLaunchState({
          ...INITIAL_LTI_LAUNCH_STATE,
          state: 'error',
          error: e,
          failedAction: 'fetch-url',
        });
      }
    }
  }, [authToken, viaUrlCallback]);

  /**
   * Fetch the assignment content URL when the app is initially displayed.
   */
  useEffect(() => {
    fetchContentUrl();
  }, [fetchContentUrl]);

  // Report a submission to the LMS, with the LMS-provided metadata needed for
  // later grading of the assignment.
  const reportSubmission = useCallback(async () => {
    // If a teacher launches an assignment or the LMS does not support reporting
    // outcomes or grading is not enabled for the assignment, then no submission
    // URL will be available.
    if (!submissionParams) {
      return;
    }

    // Don't report a submission until the URL has been successfully fetched.
    if (ltiLaunchState.state !== 'fetched-url') {
      return;
    }

    try {
      await apiCall({
        authToken,
        path: '/api/lti/submissions',
        data: submissionParams,
      });
    } catch (e) {
      // If reporting the submission failed, replace the content with an error.
      // This avoids the student trying to complete the assignment without
      // knowing that there was a problem, and the teacher then not seeing a
      // submission.
      setLtiLaunchState({
        state: 'error',
        error: e,
        failedAction: 'report-submission',
      });
    }
  }, [authToken, ltiLaunchState.state, submissionParams]);

  useEffect(reportSubmission, [reportSubmission]);

  // `AuthWindow` instance, set only when waiting for the user to approve
  // the app's access to the user's files in the LMS.
  const authWindow = useRef(null);

  /**
   * Request the user's authorization to access the content, then try fetching
   * the content URL again.
   */
  const authorizeAndFetchUrl = useCallback(async () => {
    setLtiLaunchState({
      ...INITIAL_LTI_LAUNCH_STATE,
      state: 'authorizing',
    });

    if (authWindow.current) {
      authWindow.current.focus();
      return;
    }
    authWindow.current = new AuthWindow({ authToken, authUrl, lmsName });

    try {
      await authWindow.current.authorize();
      await fetchContentUrl();
    } finally {
      // eslint-disable-next-line require-atomic-updates
      authWindow.current = null;
    }
  }, [authToken, authUrl, fetchContentUrl, lmsName]);

  if (ltiLaunchState.state === 'fetched-url') {
    return (
      <iframe width="100%" height="100%" class="js-via-iframe" src={ltiLaunchState.contentUrl} />
    );
  }

  return (
    <Fragment>
      {ltiLaunchState.state === 'fetching-url' && (
        <Spinner className="BasicLtiLaunchApp__spinner" />
      )}
      {ltiLaunchState.state === 'authorizing' && (
        <div className="BasicLtiLaunchApp__form">
          <h1 className="heading">Authorize Hypothesis</h1>
          <p>Hypothesis needs your authorization to launch this assignment.</p>
          <Button
            onClick={authorizeAndFetchUrl}
            className="BasicLtiLaunchApp__button"
            label="Authorize"
          />
        </div>
      )}
      {ltiLaunchState.state === 'error' && (
        <div className="BasicLtiLaunchApp__form">
          <h1 className="heading">Something went wrong</h1>
          <ErrorDisplay
            message="There was a problem loading this Hypothesis assignment"
            error={ltiLaunchState.error}
          />
          {ltiLaunchState.failedAction === 'fetch-url' ? (
            <Button
              onClick={authorizeAndFetchUrl}
              className="BasicLtiLaunchApp__button"
              label="Try again"
            />
          ) : (
            <b>To fix this problem, try reloading the page.</b>
          )}
        </div>
      )}
    </Fragment>
  );
}
