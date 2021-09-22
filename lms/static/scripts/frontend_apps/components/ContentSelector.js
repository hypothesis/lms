import { LabeledButton } from '@hypothesis/frontend-shared';
import { useContext, useMemo, useState } from 'preact/hooks';

import { Config } from '../config';
import {
  GooglePickerClient,
  PickerCanceledError,
} from '../utils/google-picker-client';
import { OneDrivePickerClient } from '../utils/onedrive-picker-client';

import BookPicker from './BookPicker';
import FullScreenSpinner from './FullScreenSpinner';
import LMSFilePicker from './LMSFilePicker';
import URLPicker from './URLPicker';

/**
 * @typedef {import('../api-types').Book} Book
 * @typedef {import('../api-types').File} File
 * @typedef {import('../api-types').Chapter} Chapter
 *
 * @typedef ErrorInfo
 * @prop {string} title
 * @prop {Error} error
 *
 * @typedef {'blackboardFile'|'canvasFile'|'url'|'vitalSourceBook'|null} DialogType
 *
 * @typedef {import('../utils/content-item').Content} Content
 */

/**
 * @typedef ContentSelectorProps
 * @prop {DialogType} [defaultActiveDialog] - Used for testing
 * @prop {(ei: ErrorInfo) => void} onError
 * @prop {(c: Content) => void} onSelectContent
 */

/**
 * Component that allows the user to choose the content for an assignment.
 *
 * @param {ContentSelectorProps} props
 */
export default function ContentSelector({
  defaultActiveDialog = null,
  onError,
  onSelectContent,
}) {
  const {
    api: { authToken },
    filePicker: {
      blackboard: {
        enabled: blackboardFilesEnabled,
        listFiles: blackboardListFilesApi,
      },
      canvas: { enabled: canvasFilesEnabled, listFiles: listFilesApi },
      google: {
        clientId: googleClientId,
        developerKey: googleDeveloperKey,
        origin: googleOrigin,
      },
      microsoftOneDrive: {
        enabled: oneDriveFilesEnabled,
        clientId: oneDriveClientId,
        redirectURI: oneDriveRedirectURI,
      },
      vitalSource: { enabled: vitalSourceEnabled },
    },
  } = useContext(Config);

  const [isLoadingIndicatorVisible, setLoadingIndicatorVisible] =
    useState(false);
  const [activeDialog, setActiveDialog] = useState(
    /** @type {DialogType} */ (defaultActiveDialog)
  );

  const cancelDialog = () => {
    setLoadingIndicatorVisible(false);
    setActiveDialog(null);
  };

  /** @param {DialogType} type */
  const selectDialog = type => {
    setActiveDialog(type);
  };
  // Initialize the Google Picker client if credentials have been provided.
  // We do this eagerly to make the picker load faster if the user does click
  // on the "Select from Google Drive" button.
  const googlePicker = useMemo(() => {
    if (!googleClientId || !googleDeveloperKey || !googleOrigin) {
      return null;
    }
    return new GooglePickerClient({
      developerKey: googleDeveloperKey,
      clientId: googleClientId,

      // If the form is being displayed inside an iframe, then the backend
      // must provide the URL of the top-level frame to us so we can pass it
      // to the Google Picker API. Otherwise we can use the URL of the current
      // tab.
      origin: window === window.top ? window.location.href : googleOrigin,
    });
  }, [googleDeveloperKey, googleClientId, googleOrigin]);

  // Initialize the OneDrive client if credentials have been provided.
  // We do this eagerly to make the picker load faster if the user does click
  // on the "Select from OneDrive" button.
  const oneDrivePicker = useMemo(() => {
    if (!oneDriveClientId || !oneDriveRedirectURI) {
      return null;
    }

    return new OneDrivePickerClient({
      clientId: oneDriveClientId,
      redirectURI: oneDriveRedirectURI,
    });
  }, [oneDriveClientId, oneDriveRedirectURI]);

  /** @param {string} url */
  const selectURL = url => {
    cancelDialog();
    onSelectContent({ type: 'url', url });
  };

  /** @param {File} file */
  const selectCanvasFile = file => {
    cancelDialog();
    onSelectContent({ type: 'file', file });
  };

  /** @param {File} file */
  const selectBlackboardFile = file => {
    cancelDialog();
    // file.id shall be a url of the form blackboard://content-resource/{file_id}
    onSelectContent({ type: 'url', url: file.id });
  };

  /**
   * @param {Book} book
   * @param {Chapter} chapter
   */
  const selectVitalSourceBook = (book, chapter) => {
    cancelDialog();
    onSelectContent({ type: 'vitalsource', bookID: book.id, cfi: chapter.cfi });
  };

  let dialog;
  switch (activeDialog) {
    case 'url':
      dialog = <URLPicker onCancel={cancelDialog} onSelectURL={selectURL} />;
      break;
    case 'canvasFile':
      dialog = (
        <LMSFilePicker
          authToken={authToken}
          listFilesApi={listFilesApi}
          onCancel={cancelDialog}
          onSelectFile={selectCanvasFile}
          missingFilesHelpLink="https://community.canvaslms.com/t5/Instructor-Guide/How-do-I-upload-a-file-to-a-course/ta-p/618"
        />
      );
      break;
    case 'blackboardFile':
      dialog = (
        <LMSFilePicker
          authToken={authToken}
          listFilesApi={blackboardListFilesApi}
          onCancel={cancelDialog}
          onSelectFile={selectBlackboardFile}
          // An alias we maintain that provides multiple external documentation links for
          // different versions of Blackboard (Classic vs. Ultra)
          missingFilesHelpLink={'https://web.hypothes.is/help/bb-files'}
          withBreadcrumbs
        />
      );
      break;
    case 'vitalSourceBook':
      dialog = (
        <BookPicker
          onCancel={cancelDialog}
          onSelectBook={selectVitalSourceBook}
        />
      );
      break;
    default:
      dialog = null;
  }

  const showGooglePicker = async () => {
    try {
      setLoadingIndicatorVisible(true);
      const picker = /** @type {GooglePickerClient} */ (googlePicker);
      const { id, url } = await picker.showPicker();
      await picker.enablePublicViewing(id);
      onSelectContent({ type: 'url', url });
    } catch (error) {
      setLoadingIndicatorVisible(false);
      if (!(error instanceof PickerCanceledError)) {
        console.error(error);
        onError({
          title: 'There was a problem choosing a file from Google Drive',
          error,
        });
      }
    }
  };

  const showOneDrivePicker = () => {
    setLoadingIndicatorVisible(true);
    const picker = /** @type {OneDrivePickerClient} */ (oneDrivePicker);
    /** @param {any} file */
    const success = file => {
      const sharingURL = file.value[0].permissions[0].link.webUrl;
      const url = OneDrivePickerClient.encodeSharingURL(sharingURL);
      onSelectContent({ type: 'url', url });
    };
    const cancel = () => {
      setLoadingIndicatorVisible(false);
    };
    /** @param {Error} error */
    const error = error => {
      setLoadingIndicatorVisible(false);
      console.error(error);
      onError({
        title: 'There was a problem choosing a file from OneDrive',
        error,
      });
    };
    picker.showPicker({ success, cancel, error });
  };

  return (
    <>
      {isLoadingIndicatorVisible && <FullScreenSpinner />}
      <div className="ContentSelector__actions">
        <div className="ContentSelector__actions-buttons">
          <LabeledButton
            onClick={() => selectDialog('url')}
            type="button"
            variant="primary"
            data-testid="url-button"
          >
            Enter URL of web page or PDF
          </LabeledButton>
          {canvasFilesEnabled && (
            <LabeledButton
              onClick={() => selectDialog('canvasFile')}
              variant="primary"
              data-testid="canvas-file-button"
            >
              Select PDF from Canvas
            </LabeledButton>
          )}
          {blackboardFilesEnabled && (
            <LabeledButton
              onClick={() => selectDialog('blackboardFile')}
              variant="primary"
              data-testid="blackboard-file-button"
            >
              Select PDF from Blackboard
            </LabeledButton>
          )}
          {googlePicker && (
            <LabeledButton
              onClick={showGooglePicker}
              variant="primary"
              data-testid="google-drive-button"
            >
              Select PDF from Google Drive
            </LabeledButton>
          )}
          {oneDriveFilesEnabled && (
            <LabeledButton
              onClick={showOneDrivePicker}
              variant="primary"
              data-testid="onedrive-button"
            >
              Select PDF from OneDrive
            </LabeledButton>
          )}
          {vitalSourceEnabled && (
            <LabeledButton
              onClick={() => selectDialog('vitalSourceBook')}
              variant="primary"
              data-testid="vitalsource-button"
            >
              Select book from VitalSource
            </LabeledButton>
          )}
        </div>
        <div className="u-stretch" />
      </div>
      <div>{dialog}</div>
    </>
  );
}
