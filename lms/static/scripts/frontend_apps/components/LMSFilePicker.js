import { LabeledButton, Modal } from '@hypothesis/frontend-shared';

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
    <div>
      There are no PDFs in this {documentContext}.{' '}
      <a href={href} target="_blank" rel="noreferrer">
        Upload some files to the {documentContext}
      </a>{' '}
      and try again.
    </div>
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
 * @prop {boolean} isRetry - Flag indicating that authorization has previously
 *  been attempted
 *
 * @typedef ErrorState
 * @prop {'error'} state
 * @prop {Error} error
 *
 * @typedef {FetchingState|FetchedState|AuthorizingState|ErrorState} LMSFilePickerState
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
  const [dialogState, setDialogState] = useState(
    /** @type {LMSFilePickerState} */ ({ state: 'fetching', isReload: false })
  );

  // Has the first attempt to fetch the list of files in the LMS completed?
  const [initialFetch, setInitialFetch] = useState(true);

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
    setSelectedFile(null);
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
  const fetchFiles = useCallback(
    async (isReload = false) => {
      const getNextAPICallInfo = () => {
        return folderPath[folderPath.length - 1]?.contents || listFilesApi;
      };
      try {
        setDialogState({ state: 'fetching', isReload });
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
        setDialogState({ state: 'fetched', files });
      } catch (error) {
        if (error instanceof APIError && !error.errorMessage) {
          setDialogState({ state: 'authorizing', isRetry: isReload });
        } else {
          setDialogState({ state: 'error', error });
        }
      }
      setInitialFetch(false);
    },
    [authToken, folderPath, listFilesApi]
  );

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

  /** @type {ContinueAction} */
  let continueAction;

  switch (dialogState.state) {
    case 'fetching':
      continueAction = {
        type: 'select',

        // When the user clicks the "Reload" button, we maintain the button label
        // until the file list is fetched.
        label: dialogState.isReload ? 'Reload' : 'Select',
        disabled: true,
      };
      break;
    case 'fetched':
      if (dialogState.files.length === 0) {
        continueAction = { type: 'reload' };
      } else {
        continueAction = {
          type: 'select',
          label: 'Select',
          disabled: selectedFile === null,
        };
      }
      break;
    case 'authorizing':
      continueAction = {
        type: 'authorize',
        label: dialogState.isRetry ? 'Try again' : 'Authorize',
      };
      break;
    case 'error':
      continueAction = {
        type: 'authorize',
        label: 'Try again',
      };
      break;
  }

  let continueButton;
  switch (continueAction.type) {
    case 'authorize':
      continueButton = (
        <AuthButton
          authURL={/** @type {string} */ (listFilesApi.authUrl)}
          authToken={authToken}
          label={continueAction.label}
          onAuthComplete={() => fetchFiles(true /* reload */)}
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
          onClick={() => confirmSelectedItem()}
          data-testid="select"
        >
          {continueAction.label}
        </LabeledButton>
      );
      break;
  }

  const withFileUI = ['fetching', 'fetched'].includes(dialogState.state);

  if (dialogState.state === 'fetching' && initialFetch) {
    return <FullScreenSpinner />;
  }

  return (
    <Modal
      contentClass={withFileUI ? 'LMS-Dialog--wide LMS-Dialog--tall' : ''}
      title="Select file"
      onCancel={onCancel}
      buttons={continueButton}
    >
      {dialogState.state === 'authorizing' && (
        <p data-testid="authorization warning">
          {dialogState.isRetry ? (
            <span>Unable to authorize file access.</span>
          ) : (
            <span>
              To select a file, you must authorize Hypothesis to access your
              files.
            </span>
          )}
        </p>
      )}

      {dialogState.state === 'error' && (
        <ErrorDisplay
          description="There was a problem fetching files"
          error={/** @type {Error} */ (dialogState.error)}
        />
      )}

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
            files={dialogState.state === 'fetched' ? dialogState.files : []}
            isLoading={dialogState.state === 'fetching'}
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
