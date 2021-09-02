import { Frame, LabeledButton, Modal } from '@hypothesis/frontend-shared';

import { useCallback, useEffect, useState } from 'preact/hooks';

import { APIError, apiCall } from '../utils/api';

import AuthButton from './AuthButton';
import Breadcrumbs from './Breadcrumbs';
import ErrorDisplay from './ErrorDisplay';
import FileList from './FileList';
import FullScreenSpinner from './FullScreenSpinner';

/**
 * @typedef {import("./FileList").File} File
 * @typedef {import("../config").APICallInfo} APICallInfo
 */

/**
 * @typedef NoFilesMessageProps
 * @prop {string} href - Helpful documentation URL to link to
 * @prop {boolean} inSubfolder - has the user navigated to a sub-folder?
 */

/**
 * Renders a helpful message with a link to documentation when there are no
 * uploaded files.
 *
 * @param {NoFilesMessageProps} props
 */
function NoFilesMessage({ href, inSubfolder }) {
  const documentContext = inSubfolder ? 'folder' : 'course';
  return (
    <Frame classes="LMSFilePicker__no-files">
      <div className="u-layout-column--align-center hyp-u-padding--6">
        <div>
          There are no PDFs in this {documentContext}.{' '}
          <a href={href} target="_blank" rel="noreferrer">
            Upload some files to the {documentContext}
          </a>{' '}
          and try again.
        </div>
      </div>
    </Frame>
  );
}

/**
 * @typedef LMSFilePickerProps
 * @prop {string} authToken - Auth token for use in calls to the backend
 * @prop {APICallInfo} listFilesApi -
 *   Config for the API call to list available files
 * @prop {() => any} onCancel - Callback invoked if the user cancels file selection
 * @prop {(f: File) => any} onSelectFile -
 *   Callback invoked with the metadata of the selected file if the user makes a selection
 * @prop {string} missingFilesHelpLink - A helpful URL to documentation that explains
 *   how to upload files to an LMS such as Canvas or Blackboard. This link is only shown
 *   when the API call to returns available files returns an empty list.
 * @prop {boolean} [withBreadcrumbs=false] - Render path breadcrumbs and allow
 *   sub-folder navigation?
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
  missingFilesHelpLink,
  withBreadcrumbs = false,
}) {
  // The main state of the dialog and associated data.
  const [dialogState, setDialogState] = useState(INITIAL_DIALOG_STATE);

  // Authorization attempt was made. Set after state transitions to "authorizing".
  const [authorizationAttempted, setAuthorizationAttempted] = useState(false);

  // The file or folder within `files` which is currently selected.
  const [selectedFile, setSelectedFile] = useState(
    /** @type {File|null} */ (null)
  );

  // An array of File objects representing the "path" to the current
  // list of files being displayed. This always starts at the root. The last
  // element represents the current directory path.
  const [folderPath, setFolderPath] = useState(
    /** @type {File[]} */ ([
      {
        display_name: 'Files',
        type: 'Folder',
        contents: listFilesApi,
        id: '__root__',
      },
    ])
  );

  /**
   * Change to a new folder path. This will update the breadcrumb path history
   * and cause a new fetch to be initiated to retrieve files in that folder path.
   *
   * @param {File} folder
   */
  const onChangePath = folder => {
    const currentIndex = folderPath.findIndex(file => file.id === folder.id);
    if (currentIndex >= 0) {
      // If the selected folder is already in the path, remove any entries
      // below (after) it to make it the last entry
      setFolderPath(folderPath.slice(0, currentIndex + 1));
    } else {
      // Otherwise, append it to the current path
      setFolderPath([...folderPath, folder]);
    }
  };

  // Fetches files or shows a prompt to authorize access.
  const fetchFiles = useCallback(async () => {
    const getNextAPICallInfo = () => {
      return folderPath[folderPath.length - 1]?.contents || listFilesApi;
    };
    try {
      // Show the fetching state, but preserve the existing continueAction to
      // prevent the button label changing. See:
      // https://github.com/hypothesis/lms/pull/2219#issuecomment-721833947
      setDialogState(({ continueAction, state }) => {
        // Determine the appropriate state to move to. If files have been
        // fetched, or a reload is indicated by continueAction, put the dialog
        // in a "reloading" state instead of a (fresh) "fetching" state. This
        // applies the appropriate loading state while the fetch request is in
        // flight.
        const nextState =
          state === 'fetched' ||
          state === 'reloading' ||
          continueAction === 'reload'
            ? 'reloading'
            : 'fetching';
        return {
          ...INITIAL_DIALOG_STATE,
          state: nextState,
          continueAction,
        };
      });

      const files = /** @type {File[]} */ (
        await apiCall({
          authToken,
          path: getNextAPICallInfo().path,
        })
      );

      // Handle the case in which a subsequent fetch request for a
      // different path's files was dispatched before this request resolved.
      // Give preference to the later request: If the path has changed
      // since this request was made, ignore the results of this request.
      let pathChanged = false;
      setFolderPath(path => {
        pathChanged = path !== folderPath;
        return path;
      });
      if (pathChanged) {
        return;
      }

      const continueAction =
        files.length === 0 ? 'reload' : INITIAL_DIALOG_STATE.continueAction;
      setDialogState({
        ...INITIAL_DIALOG_STATE,
        state: 'fetched',
        files,
        continueAction,
      });
    } catch (e) {
      if (e instanceof APIError && !e.errorMessage) {
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
  }, [authToken, folderPath, authorizationAttempted, listFilesApi]);

  // Update the file list any time the path changes
  useEffect(() => {
    fetchFiles();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [folderPath]);

  /** @param {File|null} file */
  const confirmSelectedItem = (file = selectedFile) => {
    if (!file) {
      return;
    }
    if (!file.type || file.type === 'File') {
      onSelectFile(file);
    } else if (file.type === 'Folder') {
      onChangePath(file);
    }
  };

  const options = {
    select: {
      continueButton: (
        <LabeledButton
          variant="primary"
          disabled={selectedFile === null}
          onClick={() => confirmSelectedItem()}
          data-testid="select"
        >
          Select
        </LabeledButton>
      ),
      warningOrError: null,
    },
    authorize: {
      continueButton: (
        <AuthButton
          authURL={/** @type {string} */ (listFilesApi.authUrl)}
          authToken={authToken}
          onAuthComplete={fetchFiles}
        />
      ),
      warningOrError: (
        <p data-testid="authorization warning">
          To select a file, you must authorize Hypothesis to access your files.
        </p>
      ),
    },
    authorize_retry: {
      continueButton: (
        <AuthButton
          authURL={/** @type {string} */ (listFilesApi.authUrl)}
          authToken={authToken}
          label="Try again"
          onAuthComplete={fetchFiles}
          data-testid="try-again"
        />
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
        <AuthButton
          authURL={/** @type {string} */ (listFilesApi.authUrl)}
          authToken={authToken}
          label="Try again"
          onAuthComplete={fetchFiles}
          data-testid="try-again"
        />
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

  const { continueButton, warningOrError } =
    options[dialogState.continueAction];

  // During the first fetch and load, we don't know yet whether we'll have
  // success fetching files, or whether we'll need auth'z or hit another
  // error. To avoid hopscotching between modals, show only
  // a full-screen spinner during this state.
  const isLoading = dialogState.state === 'fetching';
  // During subsequent file/folder fetches, represent the loading state within
  // the file list UI (do not show a full-screen spinner)
  const isReloading = dialogState.state === 'reloading';
  // Render the file list and breadcrumbs UI in certain states. This also
  // requires more real estate in the <Modal>, and applies an appropriate CSS
  // class
  const withFileUI = ['reloading', 'fetched'].includes(dialogState.state);

  if (isLoading) {
    return <FullScreenSpinner />;
  }

  return (
    <Modal
      contentClass={withFileUI ? 'LMSFilePicker' : ''}
      title={dialogState.title}
      onCancel={onCancel}
      buttons={continueButton}
    >
      {warningOrError}

      {withFileUI && (
        <>
          {withBreadcrumbs && (
            <Breadcrumbs
              items={folderPath}
              onSelectItem={onChangePath}
              renderItem={item => item.display_name}
            />
          )}
          <FileList
            files={dialogState.files ?? []}
            isLoading={isReloading}
            selectedFile={selectedFile}
            onUseFile={confirmSelectedItem}
            onSelectFile={setSelectedFile}
            noFilesMessage={
              <NoFilesMessage
                href={missingFilesHelpLink}
                inSubfolder={folderPath.length > 1}
              />
            }
          />
        </>
      )}
    </Modal>
  );
}
