import { SpinnerOverlay } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useCallback, useEffect, useRef, useState } from 'preact/hooks';

import { useConfig } from '../config';
import { isAuthorizationError, isLTILaunchServerError } from '../errors';
import type { LTILaunchServerErrorCode } from '../errors';
import { ClientRPC, useService } from '../services';
import type {
  AnnotationEventData,
  AnnotationEventType,
} from '../services/client-rpc';
import AuthWindow from '../utils/AuthWindow';
import { apiCall } from '../utils/api';
import ContentFrame from './ContentFrame';
import InstructorToolbar from './InstructorToolbar';
import LaunchErrorDialog from './LaunchErrorDialog';

/**
 * Error states managed by this component that can arise during assignment
 * launch. These affect the message that is shown to users and the actions
 * offered to remedy the problem.
 *
 * Valid error states include several known server-provided error codes as well
 * as some states applicable only to this component and its children.
 */
export type ErrorState =
  | 'error-authorizing'
  | 'error-fetching'
  | 'error-reporting-submission'
  | LTILaunchServerErrorCode;

/**
 * Application displayed when an assignment is launched if the LMS backend
 * is unable to directly render the content in an iframe. This happens when
 * the content URL needs to be fetched from a remote source (eg. the LMS's
 * file storage) first, which may require authorization from the user.
 *
 * Container elements here should take care to render at full available width
 * and height as they are the outermost containers of all LMS content.
 */
export default function BasicLTILaunchApp() {
  const {
    api: {
      authToken,
      // API callback to use to fetch the URL to show in the iframe. This is
      // needed if resolving the content URL involves potentially slow calls
      // to third party APIs (eg. the LMS's file storage).
      viaUrl: viaAPICallInfo,
      // Sync API callback and data to asynchronously load the section groups
      // to relay to the sidebar via RPC.
      sync: syncAPICallInfo,
    },
    hypothesisClient: clientConfig,
    // Content URL to show in the iframe.
    viaUrl: viaURL,
    canvas,
  } = useConfig(['api', 'hypothesisClient']);

  const clientRPC = useService(ClientRPC);

  // Canvas only: The presence of a value for this configuration property
  // indicates that an empty grading submission should be made only after this
  // (student) user performs qualifying annotation activity. Otherwise, a
  // grading submission will be made immediately upon successful launch.
  const submitAfterActivity = !!clientConfig.reportActivity;

  // Indicates what the application was doing when the error indicated by
  // `error` occurred.
  const [errorState, setErrorState] = useState<ErrorState | null>(null);

  // The most recent error that occurred when launching the assignment.
  const [error, setError] = useState<Error | null>(null);

  // URL to display in the content iframe. This is either available immediately,
  // or otherwise we'll have to make an API call to fetch it.
  const [contentURL, setContentURL] = useState<string | null>(viaURL || null);

  // Count of pending API requests which must complete before the assignment
  // content can be shown.
  const [fetchCount, setFetchCount] = useState(0);

  // The authorization URL associated with the most recent failed API call.
  const [authURL, setAuthURL] = useState<string | null>(null);

  // `AuthWindow` instance, set only when waiting for the user to approve
  // the app's access to the user's files in the LMS.
  const authWindow = useRef<AuthWindow | null>(null);

  const contentReady = !!contentURL;
  const showContent = contentReady && !errorState;
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
   * @param [authURL] - Authorization URL association with the API request
   */
  const handleError = (
    error: Error,
    state: ErrorState,
    retry = true,
    authURL?: string | null,
  ) => {
    // Here we always set the authorization URL, but we could improve UX by
    // not setting it if the problem is not related to authorization (eg.
    // a network fetch error).
    setAuthURL(authURL || null);

    if (isLTILaunchServerError(error)) {
      setError(error);
      setErrorState(error.errorCode as ErrorState);
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
      if (!syncAPICallInfo) {
        return true;
      }
      let success;

      if (updateFetchCount) {
        incFetchCount();
      }

      try {
        const groups = await apiCall<string[]>({
          authToken,
          path: syncAPICallInfo.path,
          data: syncAPICallInfo.data,
        });
        clientRPC.setGroups(groups);
        success = true;
      } catch (e) {
        handleError(
          e,
          'error-fetching',
          true /* retry */,
          syncAPICallInfo.authUrl,
        );
        success = false;
      }

      if (updateFetchCount) {
        decFetchCount();
      }

      return success;
    },
    [syncAPICallInfo, authToken, clientRPC],
  );

  /**
   * Fetch the URL of the content to display in the iframe
   */
  const fetchContentURL = useCallback(async () => {
    if (!viaAPICallInfo) {
      // If no "callback" URL was supplied for the frontend to use to fetch
      // the URL, then the backend must have provided the Via URL in the
      // initial request, which we'll just use directly.
      return true;
    }
    let success;
    incFetchCount();
    try {
      const { via_url: contentURL } = await apiCall<{ via_url: string }>({
        authToken: authToken,
        path: viaAPICallInfo.path,
      });
      setContentURL(contentURL);
      success = true;
    } catch (e) {
      handleError(
        e,
        'error-fetching',
        true /* retry */,
        viaAPICallInfo.authUrl,
      );
      success = false;
    }
    decFetchCount();
    return success;
  }, [authToken, viaAPICallInfo]);

  /**
   * Fetch the assignment content URL and groups when the app is initially displayed.
   */
  useEffect(() => {
    fetchContentURL();
    fetchGroups();
  }, [fetchContentURL, fetchGroups]);

  /**
   * Report a submission to the LMS, with the LMS-provided metadata needed for
   * later grading of the assignment.
   */
  const reportSubmission = useCallback(
    /** @param [submittedAt] - ISO8601 date for the submission */
    async (submittedAt?: string) => {
      // If a teacher launches an assignment or the LMS does not support reporting
      // outcomes or grading is not enabled for the assignment, then no submission
      // URL will be available.
      if (!canvas.speedGrader) {
        return;
      }

      // Don't submit before content is viewable
      if (!contentReady) {
        return;
      }

      const submissionParams = {
        ...canvas.speedGrader.submissionParams,
        submitted_at: submittedAt,
      };

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
        handleError(e, 'error-reporting-submission', false);
      }
    },
    [authToken, canvas.speedGrader, contentReady],
  );

  /**
   * Submit an empty grading submission on behalf of this student user. This
   * submission can happen in one of two ways:
   * - If the application is configured to do so (`submitAfterActivity`),
   *   register a callback and wait for first qualifying annotation activity
   *   before submitting.
   * - Otherwise, submit immediately.
   */
  useEffect(() => {
    if (!submitAfterActivity) {
      reportSubmission();
      return undefined;
    }

    const unsubscribe = () =>
      clientRPC.off('annotationActivity', onAnnotationActivity);

    function onAnnotationActivity(
      eventType: AnnotationEventType,
      data: AnnotationEventData,
    ) {
      if (
        ['create', 'update'].includes(eventType) &&
        data.annotation.isShared
      ) {
        reportSubmission(data.date).then(unsubscribe);
      }
    }

    clientRPC.on('annotationActivity', onAnnotationActivity);

    return unsubscribe;
  }, [clientRPC, reportSubmission, submitAfterActivity]);

  /**
   * Request the user's authorization to access the content, then try fetching
   * the content URL and groups again.
   */
  const authorizeAndFetchURL = useCallback(async () => {
    if (authWindow.current) {
      setErrorState('error-authorizing');
      authWindow.current.focus();
      return;
    }

    try {
      if (authURL) {
        setErrorState('error-authorizing');
        authWindow.current = new AuthWindow({ authToken, authUrl: authURL });
        await authWindow.current.authorize();
        setAuthURL(null);
      }
      const [fetchedContent, fetchedGroups] = await Promise.all([
        fetchContentURL(),
        fetchGroups(true /* updateFetchCount */),
      ]);
      if (fetchedContent && fetchedGroups) {
        setErrorState(null);
      }
    } finally {
      authWindow.current = null;
    }
  }, [authToken, authURL, fetchContentURL, fetchGroups]);

  return (
    <div className="h-full">
      {showSpinner && <SpinnerOverlay />}
      {errorState && (
        <LaunchErrorDialog
          busy={fetchCount > 0}
          errorState={errorState}
          error={error}
          onRetry={authorizeAndFetchURL}
        />
      )}
      <div
        className={classnames('flex flex-col h-full', {
          invisible: !showContent,
          visible: showContent,
        })}
        data-testid="content-wrapper"
      >
        <InstructorToolbar />
        <ContentFrame url={contentURL ?? ''} />
      </div>
    </div>
  );
}
