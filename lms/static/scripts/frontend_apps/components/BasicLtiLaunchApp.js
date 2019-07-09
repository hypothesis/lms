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
    urls: { via_url: viaUrl },
  } = useContext(Config);

  const [{ state, contentUrl, error }, setState] = useState({
    // The current state of the screen.
    // One of "fetching", "fetched-url", "authorizing" or "error".
    //
    // When the app is initially displayed it will attempt to fetch the content
    // URL.
    state: 'fetching-url',

    // URL of assignment content. Set when state is "fetched-url".
    contentUrl: null,

    // Details of last error. Set when state is "error".
    error: null,
  });

  /**
   * Fetch the URL of the content to display in the iframe.
   *
   * This will typically be a PDF URL proxied through Via.
   */
  const fetchContentUrl = useCallback(async () => {
    try {
      setState({ state: 'fetching-url' });
      const { via_url: contentUrl } = await apiCall({
        authToken,
        path: viaUrl,
      });
      setState({ state: 'fetched-url', contentUrl });
    } catch (e) {
      if (e instanceof ApiError && !e.errorMessage) {
        setState({ state: 'authorizing' });
      } else {
        setState({ state: 'error', error: e });
      }
    }
  }, [authToken, viaUrl]);

  /**
   * Fetch the assignment content URL when the app is initially displayed.
   */
  useEffect(() => {
    fetchContentUrl();
  }, [fetchContentUrl]);

  // `AuthWindow` instance, set only when waiting for the user to approve
  // the app's access to the user's files in the LMS.
  const authWindow = useRef(null);

  /**
   * Request the user's authorization to access the content, then try fetching
   * the content URL again.
   */
  const authorizeAndFetchUrl = useCallback(async () => {
    setState({ state: 'authorizing' });

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

  if (state === 'fetched-url') {
    return <iframe width="100%" height="100%" src={contentUrl} />;
  }

  return (
    <Fragment>
      {state === 'fetching-url' && (
        <Spinner className="BasicLtiLaunchApp__spinner" />
      )}
      {state === 'authorizing' && (
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
      {state === 'error' && (
        <div className="BasicLtiLaunchApp__form">
          <h1 className="heading">Something went wrong</h1>
          <ErrorDisplay
            message="There was a problem fetching this file"
            error={error}
          />
          <Button
            onClick={authorizeAndFetchUrl}
            className="BasicLtiLaunchApp__button"
            label="Try again"
          />
        </div>
      )}
    </Fragment>
  );
}
