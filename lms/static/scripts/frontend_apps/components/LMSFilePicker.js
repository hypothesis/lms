import { LabeledButton } from '@hypothesis/frontend-shared';
import { createElement } from 'preact';
import { useCallback, useEffect, useState } from 'preact/hooks';

import { ApiError, apiCall } from '../utils/api';

import AuthButton from './AuthButton';
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
 * @typedef FetchingState
 * @prop {'fetching'} state
 * @prop {boolean} isReload - Flag indicating that files are being re-fetched after clicking "Reload"
 *
 * @typedef FetchedState
 * @prop {'fetched'} state
 * @prop {File[]} files
 *
 * @typedef AuthorizingState
 * @prop {'authorizing'} state
 *
 * @typedef ErrorState
 * @prop {'error'} state
 * @prop {Error} error
 *
 * @typedef {FetchingState|FetchedState|AuthorizingState|ErrorState} DialogState
 */

/**
 * @typedef AuthorizeAction
 * @prop {'authorize'} type
 * @prop {string} label
 *
 * @typedef ReloadAction
 * @prop {'reload'} type
 *
 * @typedef SelectAction
 * @prop {'select'} type
 * @prop {string} label
 * @prop {boolean} disabled
 *
 * @typedef {AuthorizeAction|ReloadAction|SelectAction} ContinueAction
 */

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
  const [dialogState, setDialogState] = useState(
    /** @type {DialogState} */ ({
      state: 'fetching',
      isReload: false,
    })
  );

  // Has the first attempted to fetch the list of files in the LMS completed?
  const [initialFetch, setInitialFetch] = useState(true);

  const [selectedFile, selectFile] = useState(/** @type {File|null} */ (null));

  // Fetches files or shows a prompt to authorize access.
  const fetchFiles = useCallback(
    async (isReload = false) => {
      try {
        setDialogState({ state: 'fetching', isReload });
        const files = /** @type {File[]} */ (
          await apiCall({
            authToken,
            path: listFilesApi.path,
          })
        );
        setDialogState({ state: 'fetched', files });
      } catch (error) {
        if (error instanceof ApiError && !error.errorMessage) {
          // If the server returned an error, but provided no details, assume
          // an authorization failure.
          setDialogState({ state: 'authorizing' });
        } else {
          // Otherwise, display the error to the user.
          setDialogState({ state: 'error', error });
        }
      }
      setInitialFetch(false);
    },
    [authToken, listFilesApi]
  );

  // On the initial load, fetch files or prompt to authorize if we know that
  // authorization will be required.
  useEffect(() => {
    fetchFiles();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const useSelectedFile = () =>
    onSelectFile(/** @type {File} */ (selectedFile));

  // During the initial fetch, no dialog is rendered. This avoids UI flicker
  // due to a transition between the "fetching" state and the "authorizing" state
  // in the case where authorization is needed.
  //
  // The parent component is responsible for rendering a loading indicator behind
  // the dialog in this state.
  if (dialogState.state === 'fetching' && initialFetch) {
    return null;
  }

  // Determine the continue action for the current state.
  /** @type {ContinueAction} */
  let continueAction;
  switch (dialogState.state) {
    case 'fetching':
      continueAction = {
        type: 'select',

        // When the user clicks the "Reload" button, we maintain the button label
        // until the file list is fetched.
        label: dialogState.isReload ? 'Reload' : 'Select file',

        disabled: true,
      };
      break;
    case 'fetched':
      if (dialogState.files.length === 0) {
        continueAction = { type: 'reload' };
      } else {
        continueAction = {
          type: 'select',
          label: 'Select file',
          disabled: selectedFile === null,
        };
      }
      break;
    case 'authorizing':
      continueAction = {
        type: 'authorize',
        label: 'Authorize',
      };
      break;
    case 'error':
      continueAction = {
        type: 'authorize',
        label: 'Try again',
      };
      break;
  }

  // Render the determined continue action.
  let continueButton;
  switch (continueAction.type) {
    case 'authorize':
      continueButton = (
        <AuthButton
          authURL={/** @type {string} */ (listFilesApi.authUrl)}
          authToken={authToken}
          label={continueAction.label}
          onAuthComplete={fetchFiles}
        />
      );
      break;
    case 'reload':
      continueButton = (
        <LabeledButton
          variant="primary"
          onClick={() => fetchFiles(true /* reload */)}
          data-testid="reload"
        >
          Reload
        </LabeledButton>
      );
      break;
    case 'select':
      continueButton = (
        <LabeledButton
          variant="primary"
          disabled={continueAction.disabled}
          onClick={useSelectedFile}
          data-testid="select"
        >
          {continueAction.label}
        </LabeledButton>
      );
      break;
  }

  return (
    <Dialog
      contentClass="LMSFilePicker__dialog"
      title="Select file"
      onCancel={onCancel}
      buttons={continueButton}
    >
      {dialogState.state === 'authorizing' && (
        <p data-testid="authorization warning">
          To select a file, you must authorize Hypothesis to access your files.
        </p>
      )}

      {dialogState.state === 'error' && (
        <ErrorDisplay
          message="There was a problem fetching files"
          error={/** @type {Error} */ (dialogState.error)}
        />
      )}

      {(dialogState.state === 'fetching' ||
        dialogState.state === 'fetched') && (
        <FileList
          files={dialogState.state === 'fetched' ? dialogState.files : []}
          isLoading={dialogState.state === 'fetching'}
          selectedFile={selectedFile}
          onUseFile={onSelectFile}
          onSelectFile={selectFile}
          noFilesMessage={CanvasNoFiles} // Add Blackboard or other specific LMS warning messages here.
        />
      )}
    </Dialog>
  );
}
