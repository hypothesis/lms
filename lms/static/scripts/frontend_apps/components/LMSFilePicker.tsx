import {
  FullScreenSpinner,
  LabeledButton,
  Modal,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';

import { useCallback, useEffect, useState } from 'preact/hooks';

import type { File } from '../api-types';
import type { APICallInfo } from '../config';
import { isAuthorizationError } from '../errors';
import { apiCall } from '../utils/api';

import AuthButton from './AuthButton';
import Breadcrumbs from './Breadcrumbs';
import ErrorDisplay from './ErrorDisplay';
import FileList from './FileList';

type NoFilesMessageProps = {
  /**
   * Helpful documentation URL to link to
   */
  href: string;

  /**
   * has the user navigated to a sub-folder?
   */
  inSubfolder: boolean;
};

/**
 * Renders a helpful message with a link to documentation when there are no
 * uploaded files.
 */
function NoFilesMessage({ href, inSubfolder }: NoFilesMessageProps) {
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
   * Callback invoked with the metadata of the selected file if the user makes a selection
   */
  onSelectFile: (f: File) => void;

  /**
   * A helpful URL to documentation that explains how to upload files to an LMS such as Canvas or Blackboard.
   * This link is only shown when the API call to return available files returns an empty list.
   */
  missingFilesHelpLink: string;

  /**
   * Render path breadcrumbs and allow sub-folder navigation?
   */
  withBreadcrumbs?: boolean;
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
  files: File[];
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
}: LMSFilePickerProps) {
  const [dialogState, setDialogState] = useState<LMSFilePickerState>({
    state: 'fetching',
    isReload: false,
  });

  // Has the first attempt to fetch the list of files in the LMS completed?
  const [initialFetch, setInitialFetch] = useState(true);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // An array of File objects representing the "path" to the current
  // list of files being displayed. This always starts at the root. The last
  // element represents the current directory path.
  const [folderPath, setFolderPath] = useState<File[]>([
    {
      display_name: 'Files',
      type: 'Folder',
      contents: listFilesApi,
      id: '__root__',
    },
  ]);

  /**
   * Change to a new folder path. This will update the breadcrumb path history
   * and cause a new fetch to be initiated to retrieve files in that folder path.
   */
  const onChangePath = (folder: File) => {
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
        const files: File[] = await apiCall({
          authToken,
          path: getNextAPICallInfo().path,
        });
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
        if (isAuthorizationError(error)) {
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

  const confirmSelectedItem = (file: File | null = selectedFile) => {
    if (!file) {
      return;
    }
    if (!file.type || file.type === 'File') {
      onSelectFile(file);
    } else if (file.type === 'Folder') {
      onChangePath(file);
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
      contentClass={classnames('LMS-Dialog', {
        'LMS-Dialog--wide LMS-Dialog--tall': withFileUI,
      })}
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
