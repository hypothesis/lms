import { LabeledButton } from '@hypothesis/frontend-shared';
import { createElement } from 'preact';
import { useCallback, useEffect, useRef, useState } from 'preact/hooks';

import { ApiError, apiCall } from '../utils/api';

import AuthWindow from '../utils/AuthWindow';
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
 * @prop {'fetching'|'reloading'|'fetched'|'authorizing'|'error'} state
 * @prop {string} title - Dialog title
 * @prop {'select'|'authorize'|'authorize_retry'|'retry'|'reload'} continueAction - Action for the continue button
 * @prop {File[]|null} files - List of fetched files
 * @prop {Error|null} error - Details of current error, if `state` is 'error'
 */

/** @type {DialogState} */
const INITIAL_DIALOG_STATE = {
  state: 'fetching',
  title: 'Select a file',
  continueAction: 'select',
  files: null,
  error: null,
};

const CanvasNoFiles = (
  <div className="FileList__no-files-message">
    <p>
      There are no PDFs in this course.{' '}
      <a
        href="https://community.canvaslms.com/t5/Instructor-Guide/How-do-I-upload-a-file-to-a-course/ta-p/618"
        target="_blank"
        rel="noreferrer"
      >
        Upload some files to the course
      </a>{' '}
      and try again.
    </p>
  </div>
);

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
  /** @type {import('preact').Ref<AuthWindow>} */
  const authWindow = useRef(null);

  // Fetches files or shows a prompt to authorize access.
  const fetchFiles = useCallback(async () => {
    try {
      // Show the fetching state, but preserve the existing continueAction to
      // prevent the button label changing. See:
      // https://github.com/hypothesis/lms/pull/2219#issuecomment-721833947
      setDialogState(({ continueAction }) => ({
        ...INITIAL_DIALOG_STATE,
        state: continueAction === 'reload' ? 'reloading' : 'fetching',
        continueAction,
      }));
      const files = /** @type {File[]} */ (await apiCall({
        authToken,
        path: listFilesApi.path,
      }));
      const continueAction =
        files.length === 0 ? 'reload' : INITIAL_DIALOG_STATE.continueAction;
      setDialogState({
        ...INITIAL_DIALOG_STATE,
        state: 'fetched',
        files,
        continueAction,
      });
    } catch (e) {
      if (e instanceof ApiError && !e.errorMessage) {
        const continueAction = authorizationAttempted
          ? 'authorize_retry'
          : 'authorize';

        // If the server returned an error, but provided no details, assume
        // an authorization failure.
        setDialogState({
          ...INITIAL_DIALOG_STATE,
          state: 'authorizing',
          title: 'Allow file access',
          continueAction,
        });
        setAuthorizationAttempted(true);
      } else {
        // Otherwise, display the error to the user.
        setDialogState({
          ...INITIAL_DIALOG_STATE,
          state: 'error',
          title: 'Error accessing files',
          error: e,
          continueAction: 'retry',
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
      authWindow.current.close();
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

  const options = {
    select: {
      continueButton: (
        <LabeledButton
          variant="primary"
          disabled={selectedFile === null}
          onClick={useSelectedFile}
          data-testid="select"
        >
          Select
        </LabeledButton>
      ),
      warningOrError: null,
    },
    authorize: {
      continueButton: (
        <LabeledButton
          onClick={authorizeAndFetchFiles}
          variant="primary"
          data-testid="authorize"
        >
          Authorize
        </LabeledButton>
      ),
      warningOrError: (
        <p data-testid="authorization warning">
          To select a file, you must authorize Hypothesis to access your files.
        </p>
      ),
    },
    authorize_retry: {
      continueButton: (
        <LabeledButton
          onClick={authorizeAndFetchFiles}
          variant="primary"
          data-testid="try-again"
        >
          Try again
        </LabeledButton>
      ),
      warningOrError: (
        <ErrorDisplay
          message={'Failed to authorize file access'}
          error={new Error('')}
        />
      ),
    },
    retry: {
      continueButton: (
        <LabeledButton
          onClick={authorizeAndFetchFiles} // maybe it should use fetchFile function instead
          variant="primary"
          data-testid="try-again"
        >
          Try again
        </LabeledButton>
      ),
      warningOrError: (
        <ErrorDisplay
          message="There was a problem fetching files"
          error={/** @type {Error} */ (dialogState.error)}
        />
      ),
    },
    reload: {
      continueButton: (
        <LabeledButton
          disabled={dialogState.state === 'reloading'}
          onClick={fetchFiles}
          variant="primary"
          data-testid="reload"
        >
          Reload
        </LabeledButton>
      ),
      warningOrError: null,
    },
  };

  const { continueButton, warningOrError } = options[
    dialogState.continueAction
  ];

  if (dialogState.state === 'fetching') {
    return null;
  }

  return (
    <Dialog
      contentClass="LMSFilePicker__dialog"
      title={dialogState.title}
      onCancel={cancel}
      buttons={continueButton}
    >
      {warningOrError}

      {['reloading', 'fetched'].includes(dialogState.state) && (
        <FileList
          files={dialogState.files ?? []}
          isLoading={dialogState.state === 'reloading'}
          selectedFile={selectedFile}
          onUseFile={onSelectFile}
          onSelectFile={selectFile}
          noFilesMessage={CanvasNoFiles} // Add Blackboard or other specific LMS warning messages here.
        />
      )}
    </Dialog>
  );
}
