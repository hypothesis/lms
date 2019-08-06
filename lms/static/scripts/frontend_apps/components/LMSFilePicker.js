import { Fragment, createElement } from 'preact';
import { useCallback, useEffect, useRef, useState } from 'preact/hooks';
import propTypes from 'prop-types';

import { ApiError, listFiles } from '../utils/api';

import AuthWindow from '../utils/AuthWindow';
import Button from './Button';
import Dialog from './Dialog';
import ErrorDisplay from './ErrorDisplay';
import FileList from './FileList';

const INITIAL_DIALOG_STATE = {
  // The current state of the dialog, one of:
  // "fetching", "fetched", "authorizing" or "error".
  state: 'fetching',

  // List of fetched files. Set when state is "fetched".
  files: null,

  // Fetch error details. Set when state is "error".
  error: null,
};

/**
 * A file picker dialog that allows the user to choose files from their
 * LMS's file storage.
 *
 * The picker will attempt to list files when mounted, and will show an
 * authorization popup if necessary.
 */
export default function LMSFilePicker({
  authToken,
  authUrl,
  courseId,
  lmsName,
  registeredLmsUrl,
  onCancel,
  onSelectFile,
}) {
  // The main state of the dialog and associated data.
  const [dialogState, setDialogState] = useState(INITIAL_DIALOG_STATE);

  // Authorization attempt was made. Set after state transitions to "authorizing".
  const [authorizationAttempted, setAuthorizationAttempted] = useState(false);

  // The file within `files` which is currently selected.
  const [selectedFile, selectFile] = useState(null);

  // `AuthWindow` instance, set only when waiting for the user to approve
  // the app's access to the user's files in the LMS.
  const authWindow = useRef(null);

  // Fetches files or shows a prompt to authorize access.
  const fetchFiles = useCallback(async () => {
    try {
      setDialogState({ ...INITIAL_DIALOG_STATE, state: 'fetching' });
      const files = await listFiles(authToken, courseId);
      setDialogState({ ...INITIAL_DIALOG_STATE, state: 'fetched', files });
    } catch (e) {
      if (e instanceof ApiError && !e.errorMessage) {
        // If the server returned an error, but provided no details, assume
        // an authorization failure.
        setDialogState({ ...INITIAL_DIALOG_STATE, state: 'authorizing' });
      } else {
        // Otherwise, display the error to the user.
        setDialogState({ ...INITIAL_DIALOG_STATE, state: 'error', error: e });
      }
    }
  }, [authToken, courseId]);

  // Execute the authorization flow in a popup window and then attempt to
  // fetch files.
  const authorizeAndFetchFiles = useCallback(async () => {
    setDialogState({ ...INITIAL_DIALOG_STATE, state: 'authorizing' });
    setAuthorizationAttempted(true);

    if (authWindow.current) {
      authWindow.current.focus();
      return;
    }

    authWindow.current = new AuthWindow({ authToken, authUrl, lmsName });

    try {
      await authWindow.current.authorize();
      await fetchFiles();
    } finally {
      authWindow.current.close();
      // eslint-disable-next-line require-atomic-updates
      authWindow.current = null;
    }
  }, [fetchFiles, authToken, authUrl, lmsName]);

  // On the initial load, fetch files or prompt to authorize if we know that
  // authorization will be required.
  useEffect(() => {
    if (dialogState.state === 'authorizing') {
      authorizeAndFetchFiles();
    } else {
      fetchFiles();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const cancel = () => {
    if (authWindow.current) {
      authWindow.current.close();
    }
    onCancel();
  };

  const useSelectedFile = () => onSelectFile(selectedFile);

  const title =
    dialogState.state === 'authorizing' ? 'Allow file access' : 'Select a file';

  return (
    <Dialog
      contentClass="LMSFilePicker__dialog"
      title={title}
      onCancel={cancel}
      buttons={[
        dialogState.state === 'authorizing' || dialogState.state === 'error' ? (
          <Button
            key="showAuthWindow"
            onClick={authorizeAndFetchFiles}
            label={
              dialogState.state === 'error' ||
              (dialogState.state === 'authorizing' && authorizationAttempted)
                ? 'Try again'
                : 'Authorize'
            }
          />
        ) : (
          <Button
            key="select"
            disabled={selectedFile === null}
            onClick={useSelectedFile}
            label="Select"
          />
        ),
      ]}
    >
      {dialogState.state === 'error' && (
        <ErrorDisplay
          message="There was a problem fetching files"
          error={dialogState.error}
        />
      )}
      {dialogState.state === 'authorizing' && authorizationAttempted && (
        <ErrorDisplay
          message=<Fragment>
            <a>{`Failed to authorize with the ${lmsName} instance at `}</a>
            <a href={`${registeredLmsUrl}`}>{`${registeredLmsUrl}`}</a>
          </Fragment>
          error={new Error('')}
        />
      )}
      {dialogState.state === 'authorizing' && !authorizationAttempted && (
        <p>
          To select a file, you must authorize Hypothesis to access your files
          in {lmsName}.
        </p>
      )}
      {(dialogState.state === 'fetching' ||
        dialogState.state === 'fetched') && (
        <FileList
          files={dialogState.files || []}
          isLoading={dialogState.state === 'fetching'}
          selectedFile={selectedFile}
          onUseFile={onSelectFile}
          onSelectFile={selectFile}
        />
      )}
    </Dialog>
  );
}

LMSFilePicker.propTypes = {
  /**
   * Auth token for use in calls to the backend.
   */
  authToken: propTypes.string,

  /**
   * URL of the authorization endpoint.
   */
  authUrl: propTypes.string,

  /**
   * ID of the course that the user is choosing a file for.
   */
  courseId: propTypes.string.isRequired,

  /**
   * The name of the LMS to display in API controls, eg. "Canvas".
   */
  lmsName: propTypes.string.isRequired,

  /**
   * The url of the LMS, eg. "https://foobar.instructure.com".
   */
  registeredLmsUrl: propTypes.string.isRequired,

  /** Callback invoked if the user cancels file selection. */
  onCancel: propTypes.func.isRequired,

  /**
   * Callback invoked with the metadata of the selected file if the user makes
   * a selection.
   */
  onSelectFile: propTypes.func.isRequired,
};
