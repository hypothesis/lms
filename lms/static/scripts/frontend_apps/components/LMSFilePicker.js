import { createElement } from 'preact';
import { useCallback, useEffect, useRef, useState } from 'preact/hooks';

import { ApiError, apiCall } from '../utils/api';

import AuthWindow from '../utils/AuthWindow';
import Button from './Button';
import Dialog from './Dialog';
import ErrorDisplay from './ErrorDisplay';
import FileList from './FileList';

/**
 * @typedef {import("./FileList").File} File
 * @typedef {import("../config").ApiCallInfo} ApiCallInfo
 */

/**
 * @typedef LMSFilePickerProps
 * @prop {string} authToken - Auth token for use in calls to the backend
 * @prop {ApiCallInfo} listFilesApi -
 *   Config for the API call to list available files
 * @prop {() => any} onCancel - Callback invoked if the user cancels file selection
 * @prop {(f: File) => any} onSelectFile -
 *   Callback invoked with the metadata of the selected file if the user makes a selection
 */

/**
 * @typedef DialogState
 * @prop {'fetching'|'fetched'|'authorizing'|'error'} state
 * @prop {string} title - Dialog title
 * @prop {'select'|'authorize'|'authorize_retry'|'retry'|'none'} buttonAction - Action for the right button
 * @prop {File[]|null} files - List of fetched files
 * @prop {Error|null} error - Details of current error, if `state` is 'error'
 */

/** @type {DialogState} */
const INITIAL_DIALOG_STATE = {
  state: 'fetching',
  title: 'Select a file',
  buttonAction: 'select',
  files: null,
  error: null,
};

/**
 * A file picker dialog that allows the user to choose files from their
 * LMS's file storage.
 *
 * The picker will attempt to list files when mounted, and will show an
 * authorization popup if necessary.
 *
 * @param {LMSFilePickerProps} props
 */
export default function LMSFilePicker({
  authToken,
  listFilesApi,
  onCancel,
  onSelectFile,
}) {
  // The main state of the dialog and associated data.
  const [dialogState, setDialogState] = useState(INITIAL_DIALOG_STATE);

  // Authorization attempt was made. Set after state transitions to "authorizing".
  const [authorizationAttempted, setAuthorizationAttempted] = useState(false);

  // The file within `files` which is currently selected.
  const [selectedFile, selectFile] = useState(/** @type {File|null} */ (null));

  // `AuthWindow` instance, set only when waiting for the user to approve
  // the app's access to the user's files in the LMS.
  const authWindow = useRef(/** @type {AuthWindow|null} */ (null));

  // Fetches files or shows a prompt to authorize access.
  const fetchFiles = useCallback(async () => {
    try {
      setDialogState({ ...INITIAL_DIALOG_STATE, state: 'fetching' });
      const files = /** @type {File[]} */ (await apiCall({
        authToken,
        path: listFilesApi.path,
      }));
      const title =
        files.length === 0 ? 'No files available' : INITIAL_DIALOG_STATE.title;
      const buttonAction =
        files.length === 0 ? 'none' : INITIAL_DIALOG_STATE.buttonAction;
      setDialogState({
        ...INITIAL_DIALOG_STATE,
        state: 'fetched',
        files,
        title,
        buttonAction,
      });
    } catch (e) {
      const buttonAction = authorizationAttempted
        ? 'authorize_retry'
        : 'authorize';
      if (e instanceof ApiError && !e.errorMessage) {
        // If the server returned an error, but provided no details, assume
        // an authorization failure.
        setDialogState({
          ...INITIAL_DIALOG_STATE,
          state: 'authorizing',
          title: 'Allow file access',
          buttonAction,
        });
      } else {
        // Otherwise, display the error to the user.
        setDialogState({
          ...INITIAL_DIALOG_STATE,
          state: 'error',
          title: 'Error accessing files',
          error: e,
          buttonAction: 'retry',
        });
      }
    }
  }, [authToken, listFilesApi, authorizationAttempted]);

  // Execute the authorization flow in a popup window and then attempt to
  // fetch files.
  const authorizeAndFetchFiles = useCallback(async () => {
    if (authWindow.current) {
      authWindow.current.focus();
      return;
    }

    // We assume here that the API call to list files will always require
    // authentication. This is true for the LMSes (Canvas, Blackboard) that
    // we currently support.
    const authUrl = /** @type {string} */ (listFilesApi.authUrl);
    authWindow.current = new AuthWindow({ authToken, authUrl });

    try {
      await authWindow.current.authorize();
      await fetchFiles();
    } finally {
      setAuthorizationAttempted(true);
      authWindow.current.close();
      // eslint-disable-next-line require-atomic-updates
      // @ts-ignore - `authWindow` is marked as non-nullable.
      authWindow.current = null;
    }
  }, [fetchFiles, authToken, listFilesApi]);

  // On the initial load, fetch files or prompt to authorize if we know that
  // authorization will be required.
  useEffect(() => {
    fetchFiles();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const cancel = () => {
    if (authWindow.current) {
      authWindow.current.close();
    }
    onCancel();
  };

  const useSelectedFile = () =>
    onSelectFile(/** @type {File} */ (selectedFile));

  let buttons;
  switch (dialogState.buttonAction) {
    case 'select':
      buttons = [
        <Button
          key="select"
          disabled={selectedFile === null}
          onClick={useSelectedFile}
          label="Select"
        />,
      ];
      break;
    case 'authorize':
      buttons = [
        <Button
          key="showAuthWindow"
          onClick={authorizeAndFetchFiles}
          label="Authorize"
        />,
      ];
      break;
    case 'authorize_retry':
      buttons = [
        <Button
          key="showAuthWindow"
          onClick={authorizeAndFetchFiles}
          label="Try authorize again"
        />,
      ];
      break;
    case 'retry':
      buttons = [<Button key="retry" onClick={fetchFiles} label="Try again" />];
      break;
    default:
      buttons = [];
      break;
  }

  return (
    <Dialog
      contentClass="LMSFilePicker__dialog"
      title={dialogState.title}
      onCancel={cancel}
      buttons={buttons}
    >
      {dialogState.state === 'error' && (
        <ErrorDisplay
          message="There was a problem fetching files"
          error={/** @type {Error} */ (dialogState.error)}
        />
      )}
      {dialogState.state === 'authorizing' && authorizationAttempted && (
        <ErrorDisplay
          message={'Failed to authorize with Canvas'}
          error={new Error('')}
        />
      )}
      {dialogState.state === 'authorizing' && !authorizationAttempted && (
        <p>
          To select a file, you must authorize Hypothesis to access your files
          in Canvas.
        </p>
      )}

      {['fetching', 'fetched'].includes(dialogState.state) && (
        <FileList
          files={dialogState.files ?? []}
          isLoading={dialogState.state === 'fetching'}
          selectedFile={selectedFile}
          onUseFile={onSelectFile}
          onSelectFile={selectFile}
        />
      )}
    </Dialog>
  );
}
