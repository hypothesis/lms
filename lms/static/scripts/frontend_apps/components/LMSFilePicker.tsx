import {
  Button,
  ModalDialog,
  SpinnerOverlay,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useCallback, useEffect, useState } from 'preact/hooks';

import type { File, Folder } from '../api-types';
import type { APICallInfo } from '../config';
import { isAuthorizationError } from '../errors';
import { apiCall } from '../utils/api';
import AuthButton from './AuthButton';
import Breadcrumbs from './Breadcrumbs';
import DocumentList from './DocumentList';
import ErrorDisplay from './ErrorDisplay';

type NoFilesMessageProps = {
  /**
   * Helpful documentation URL to link to
   */
  href: string;

  /**
   * has the user navigated to a sub-folder?
   */
  inSubfolder: boolean;

  documentType: 'file' | 'page' | 'video';
};

/**
 * Renders a helpful message with a link to documentation when there are no
 * uploaded files.
 */
function NoFilesMessage({
  href,
  inSubfolder,
  documentType,
}: NoFilesMessageProps) {
  const documentContext = inSubfolder ? 'folder' : 'course';

  let action;
  switch (documentType) {
    case 'file':
      action = `Upload some files to the ${documentContext}`;
      break;
    case 'page':
      action = `Create some pages in the ${documentContext}`;
      break;
    case 'video':
      action = `Upload some videos to the ${documentContext}`;
      break;
  }

  return (
    <div>
      There are no {documentType}s in this {documentContext}.{' '}
      <a href={href} target="_blank" rel="noreferrer">
        {action}
      </a>{' '}
      and try again.
    </div>
  );
}

type LMSFilePickerProps = {
  /**
   * Auth token for use in calls to the backend
   */
  authToken: string;

  /**
   * Config for the API call to list available files
   */
  listFilesApi: APICallInfo;

  /**
   * Callback invoked if the user cancels file selection
   */
  onCancel: () => any;

  /**
   * Callback invoked with the metadata of the selected document if the user makes a selection
   */
  onSelectFile: (file: File) => void;

  /**
   * A helpful URL to documentation that explains how to upload files to an LMS such as Canvas or Blackboard.
   * This link is only shown when the API call to return available files returns an empty list.
   */
  missingFilesHelpLink: string;

  /**
   * Render path breadcrumbs and allow sub-folder navigation?
   */
  withBreadcrumbs?: boolean;

  /**
   * The type of documents handled by the file picker, which can influence user-facing messages.
   * Defaults to 'file'
   */
  documentType?: 'file' | 'page' | 'video';
};

type FetchingState = {
  state: 'fetching';

  /**
   * Flag indicating that files are being re-fetched after clicking "Reload"
   */
  isReload: boolean;
};

type FetchedState = {
  state: 'fetched';
  files: Array<File | Folder>;
};

type AuthorizingState = {
  state: 'authorizing';

  /**
   * Flag indicating that authorization has previously been attempted
   */
  isRetry: boolean;
};

type ErrorState = {
  state: 'error';
  error: Error;
};

type LMSFilePickerState =
  | FetchingState
  | FetchedState
  | AuthorizingState
  | ErrorState;

type AuthorizeAction = {
  type: 'authorize';
  label: string;
};

type ReloadAction = {
  type: 'reload';
};

type SelectAction = {
  type: 'select';
  label: string;
  disabled: boolean;
};

type ContinueAction = AuthorizeAction | ReloadAction | SelectAction;

/**
 * A file picker dialog that allows the user to choose files from their
 * LMS's file storage.
 *
 * The picker will attempt to list files when mounted, and will show an
 * authorization popup if necessary.
 */
export default function LMSFilePicker({
  authToken,
  listFilesApi,
  onCancel,
  onSelectFile,
  missingFilesHelpLink,
  withBreadcrumbs = false,
  documentType = 'file',
}: LMSFilePickerProps) {
  const [dialogState, setDialogState] = useState<LMSFilePickerState>({
    state: 'fetching',
    isReload: false,
  });

  // Has the first attempt to fetch the list of files in the LMS completed?
  const [initialFetch, setInitialFetch] = useState(true);

  const [selectedFile, setSelectedFile] = useState<File | Folder | null>(null);

  // Array of Folder objects representing the "path" to the current list of
  // files being displayed. This always starts at the root. The last element
  // represents the current directory path.  Every item can potentially have
  // `children`. In that case we'll retrieve those without querying the API when
  // the folder becomes active.
  const [folderPath, setFolderPath] = useState<Folder[]>([
    {
      display_name: 'Files',
      type: 'Folder',
      contents: listFilesApi,
      id: '__root__',
    },
  ]);

  /**
   * Change to a new folder path. This will update the breadcrumb path history
   * and cause displayed files to be re-computed for that folder path.
   */
  const onChangePath = (folder: Folder) => {
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

  const loadFilesToDisplay = useCallback(
    /**
     * Retrieve the files for the active directory, either by returning an
     * appropriate subset of previously-loaded files, or by fetching a file
     * listing from the API.
     *
     * @param isReload - When true, force a fetch of file listings from the API,
     *   even if files were previously loaded.
     */
    async (isReload = false) => {
      const getNextAPICallInfo = () =>
        folderPath[folderPath.length - 1]?.contents || listFilesApi;
      const loadFilesFromAPI = (): Promise<Array<File | Folder>> =>
        apiCall({
          authToken,
          path: getNextAPICallInfo().path,
        });

      const children = folderPath[folderPath.length - 1]?.children;
      if (!isReload && children) {
        // The files in this directory were loaded by an earlier fetch
        return children;
      }

      const loadedFiles = await loadFilesFromAPI();
      const [, ...activePathWithoutRoot] = folderPath;
      let filesForFolder = loadedFiles;

      // Ensure we only return the files for the active directory.
      //
      // Depending on the LMS API being used, the loaded files could be either:
      // 1. A flat list of files and folders for the active directory only, or
      // 2. A full tree of all files and folders
      //
      // In the first case (flat list), we can return the `loadedFiles`
      // directly. To handle the second case (tree), we need to search the tree
      // for just those files and folders that are within the currently-active
      // directory.
      for (const folder of activePathWithoutRoot) {
        const folderFound = filesForFolder.find(
          fileOrFolder => fileOrFolder.id === folder.id,
        ) as Folder | undefined;
        if (folderFound?.children) {
          filesForFolder = folderFound.children;
        }
      }

      return filesForFolder;
    },
    [authToken, folderPath, listFilesApi],
  );

  const computeFilesToDisplay = useCallback(
    /**
     * Compute the correct list of files to display in the picker. Handle error
     * states if they arise.
     *
     * @param isReload - When true, request a fresh fetch of files from the API
     */
    async (isReload = false) => {
      try {
        setDialogState({ state: 'fetching', isReload });
        const files = await loadFilesToDisplay(isReload);

        // Handle the case in which a subsequent fetch request for a
        // different path's files was dispatched before this request resolved.
        // Give preference to the later request: If the path has changed
        // since this request was made, ignore the results of this request.
        let pathChanged = false;
        setFolderPath(path => {
          pathChanged = path !== folderPath;
          return path;
        });
        // ESLint doesn't know that `setFolderPath` runs its callback synchronously.
        // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
        if (pathChanged) {
          return;
        }
        setDialogState({ state: 'fetched', files });
      } catch (error) {
        if (isAuthorizationError(error)) {
          setDialogState({ state: 'authorizing', isRetry: isReload });
        } else {
          setDialogState({ state: 'error', error });
        }
      }
      setInitialFetch(false);
    },
    [folderPath, loadFilesToDisplay],
  );

  // Re-compute the file list any time the path changes
  useEffect(() => {
    computeFilesToDisplay();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [folderPath]);

  const confirmSelectedItem = (file: File | Folder | null = selectedFile) => {
    if (!file) {
      return;
    }
    if (file.type === 'Folder') {
      onChangePath(file);
    } else {
      onSelectFile(file);
    }
  };

  let continueAction: ContinueAction;

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
          authURL={listFilesApi.authUrl!}
          authToken={authToken}
          label={continueAction.label}
          onAuthComplete={() => computeFilesToDisplay(true /* reload */)}
        />
      );
      break;
    case 'reload':
      continueButton = (
        <Button
          variant="primary"
          onClick={() => computeFilesToDisplay(true /* reload */)}
          data-testid="reload"
        >
          Reload
        </Button>
      );
      break;
    case 'select':
      continueButton = (
        <Button
          variant="primary"
          disabled={continueAction.disabled}
          onClick={() => confirmSelectedItem()}
          data-testid="select"
        >
          {continueAction.label}
        </Button>
      );
      break;
  }

  const withFileUI = ['fetching', 'fetched'].includes(dialogState.state);

  if (dialogState.state === 'fetching' && initialFetch) {
    return <SpinnerOverlay />;
  }

  return (
    <ModalDialog
      classes={classnames({
        // Set a fixed height on the modal when displaying a list of files.
        // This prevents the height of the modal changing as items are loaded.
        'h-[25rem]': withFileUI,
      })}
      title={`Select ${documentType}`}
      onClose={onCancel}
      closeTitle="Close document picker"
      size="lg"
      buttons={[
        <Button data-testid="cancel-button" key="cancel" onClick={onCancel}>
          Cancel
        </Button>,
        continueButton,
      ]}
      // The FileList UI handles its own (partial-content) scrolling
      scrollable={!withFileUI}
    >
      {dialogState.state === 'authorizing' && (
        <p data-testid="authorization warning">
          {dialogState.isRetry ? (
            <span>Unable to authorize file access.</span>
          ) : (
            <span>
              To select a {documentType}, you must authorize Hypothesis to
              access your {documentType}s.
            </span>
          )}
        </p>
      )}

      {dialogState.state === 'error' && (
        <ErrorDisplay
          description={`There was a problem fetching ${documentType}s`}
          error={dialogState.error}
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
          <DocumentList
            title={`List of ${documentType}s`}
            documents={dialogState.state === 'fetched' ? dialogState.files : []}
            isLoading={dialogState.state === 'fetching'}
            selectedDocument={selectedFile}
            onUseDocument={confirmSelectedItem}
            onSelectDocument={setSelectedFile}
            noDocumentsMessage={
              <NoFilesMessage
                href={missingFilesHelpLink}
                inSubfolder={folderPath.length > 1}
                documentType={documentType}
              />
            }
          />
        </>
      )}
    </ModalDialog>
  );
}
