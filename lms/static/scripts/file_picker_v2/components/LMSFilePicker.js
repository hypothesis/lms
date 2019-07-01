import { createElement } from 'preact';
import { useCallback, useEffect, useRef, useState } from 'preact/hooks';
import propTypes from 'prop-types';

import AuthWindow from '../utils/AuthWindow';
import Button from './Button';
import Dialog from './Dialog';
import FileList from './FileList';
import { AuthorizationError, listFiles } from '../utils/api';

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
  isAuthorized,
  lmsName,
  onAuthorized,
  onCancel,
  onSelectFile,
}) {
  /** The array of files returned by a call to `listFiles`. */
  const [files, setFiles] = useState([]);

  /** Set to `true` if the list of files is being fetched. */
  const [isLoading, setLoading] = useState(true);

  /**
   * `true` if we are waiting for the user to authorize the app's access
   * to files in the LMS.
   */
  const [isAuthorizing, setAuthorizing] = useState(!isAuthorized);

  /** The file within `files` which is currently selected. */
  const [selectedFile, selectFile] = useState(null);

  // `AuthWindow` instance, set only when waiting for the user to approve
  // the app's access to the user's files in the LMS.
  const authWindow = useRef(null);

  // Fetches files or shows a prompt to authorize access.
  const fetchFiles = useCallback(async () => {
    setAuthorizing(false);
    try {
      setLoading(true);
      const files = await listFiles(authToken, courseId);
      setLoading(false);
      setFiles(files);
    } catch (e) {
      // TODO - Handle non-auth errors from the `listFiles` call.
      if (e instanceof AuthorizationError) {
        // Show authorization prompt.
        setAuthorizing(true);
      }
    }
  }, [authToken, courseId]);

  // Execute the authorization flow in a popup window and then attempt to
  // fetch files.
  const authorizeAndFetchFiles = useCallback(async () => {
    setAuthorizing(true);

    if (authWindow.current) {
      authWindow.current.focus();
      return;
    }

    authWindow.current = new AuthWindow({ authToken, authUrl, lmsName });

    try {
      await authWindow.current.authorize();
      await fetchFiles();

      if (onAuthorized) {
        onAuthorized();
      }
    } finally {
      authWindow.current.close();
      // eslint-disable-next-line require-atomic-updates
      authWindow.current = null;
    }
  }, [fetchFiles, authToken, authUrl, lmsName, onAuthorized]);

  // On the initial load, fetch files or prompt to authorize if we know that
  // authorization will be required.
  useEffect(() => {
    if (isAuthorizing) {
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

  const title = isAuthorizing ? 'Allow file access' : 'Select a file';

  return (
    <Dialog
      contentClass="LMSFilePicker__dialog"
      title={title}
      onCancel={cancel}
      buttons={[
        isAuthorizing ? (
          <Button
            key="showAuthWindow"
            onClick={authorizeAndFetchFiles}
            label="Authorize"
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
      {isAuthorizing && (
        <p>
          To select a file, you must authorize Hypothesis to access your files
          in {lmsName}.
        </p>
      )}
      {!isAuthorizing && (
        <FileList
          files={files}
          isLoading={isLoading}
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
   * A hint as to whether the backend believes the user has authorized our
   * LMS app's access to the user's files in the LMS.
   */
  isAuthorized: propTypes.bool,

  /**
   * The name of the LMS to display in API controls, eg. "Canvas".
   */
  lmsName: propTypes.string.isRequired,

  /** Callback invoked if the user cancels file selection. */
  onCancel: propTypes.func.isRequired,

  /**
   * Callback invoked with the metadata of the selected file if the user makes
   * a selection.
   */
  onSelectFile: propTypes.func.isRequired,

  /**
   * Callback invoked when authorization succeeds. The parent component can
   * use this to update the `isAuthorized` hint if the dialog is closed and
   * then later shown again.
   */
  onAuthorized: propTypes.func,
};
