import { FullScreenSpinner } from '@hypothesis/frontend-shared';
import classNames from 'classnames';

import {
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'preact/hooks';

import { Config } from '../config';
import { isAuthorizationError, isLTILaunchServerError } from '../errors';
import { ClientRPC, useService } from '../services';
import { apiCall } from '../utils/api';
import AuthWindow from '../utils/AuthWindow';

import LMSGrader from './LMSGrader';
import LaunchErrorDialog from './LaunchErrorDialog';
import VitalSourceBookViewer from './VitalSourceBookViewer';

/**
 * Error states managed by this component that can arise during assignment
 * launch. These affect the message that is shown to users and the actions
 * offered to remedy the problem.
 *
 * Valid error states include several known server-provided error codes as well
 * as some states applicable only to this component and its children.
 *
 * @typedef {'error-authorizing'|
 *           'error-fetching'|
 *           'error-reporting-submission'|
 *           import('../errors').LTILaunchServerErrorCode} ErrorState
 */

/**
 * Application displayed when an assignment is launched if the LMS backend
 * is unable to directly render the content in an iframe. This happens when
 * the content URL needs to be fetched from a remote source (eg. the LMS's
 * file storage) first, which may require authorization from the user.
 */
export default function BasicLTILaunchApp() {
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
    vitalSource: vitalSourceConfig,
  } = useContext(Config);

  const clientRPC = useService(ClientRPC);

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
  const showIframe = (contentUrl || vitalSourceConfig) && !errorState;

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
   * @param {Error} error - Error object from request.
   * @param {ErrorState} state
   * @param {boolean} [retry=true] - Can the request be retried?
   * @param {string} [authUrl] -
   *   Authorization URL association with the API request
   */
  const handleError = (error, state, retry = true, authUrl) => {
    // Here we always set the authorization URL, but we could improve UX by
    // not setting it if the problem is not related to authorization (eg.
    // a network fetch error).
    setAuthUrl(authUrl || null);

    if (isLTILaunchServerError(error)) {
      setError(error);
      setErrorState(/** @type {ErrorState} */ (error.errorCode));
    } else if (isAuthorizationError(error) && retry) {
      setErrorState('error-authorizing');
    } else {
      // Handle other types of errors, which may be APIError or Error
      setError(error);
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
        clientRPC.setGroups(groups);
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
    [apiSync, authToken, clientRPC]
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

    // Don't report a submission until we have the data needed to display the assignment content
    // contentUrl will be resolved from an API call to viaUrlApi.path except on VitalSource assignments
    // where vitalSourceConfig will be present directly on the config instead.
    if (!contentUrl && !vitalSourceConfig) {
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
  }, [authToken, canvas.speedGrader, contentUrl, vitalSourceConfig]);

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

  // Construct the <iframe> content
  let iFrameWrapper;
  const iFrame = vitalSourceConfig ? (
    <VitalSourceBookViewer
      launchUrl={vitalSourceConfig.launchUrl}
      launchParams={vitalSourceConfig.launchParams}
    />
  ) : (
    <iframe
      className="BasicLTILaunchApp__iframe hyp-u-border"
      src={contentUrl || ''}
      title="Course content with Hypothesis annotation viewer"
    />
  );

  if (grading && grading.enabled) {
    // Use the LMS Grader
    iFrameWrapper = (
      <LMSGrader
        clientRPC={clientRPC}
        apiSync={apiSync}
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
      className={classNames('BasicLTILaunchApp__content', {
        'is-hidden': !showIframe,
      })}
    >
      {iFrameWrapper}
    </div>
  );

  return (
    <div className="BasicLTILaunchApp">
      {showSpinner && <FullScreenSpinner />}
      {errorState && (
        <LaunchErrorDialog
          busy={fetchCount > 0}
          errorState={errorState}
          error={error}
          onRetry={authorizeAndFetchUrl}
        />
      )}
      {content}
    </div>
  );
}
