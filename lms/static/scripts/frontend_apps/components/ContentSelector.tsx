import { Button, SpinnerOverlay } from '@hypothesis/frontend-shared/lib/next';
import { useMemo, useState } from 'preact/hooks';

import type { Book, File, Chapter } from '../api-types';
import { useConfig } from '../config';
import { PickerCanceledError } from '../errors';
import type { Content } from '../utils/content-item';
import { GooglePickerClient } from '../utils/google-picker-client';
import { OneDrivePickerClient } from '../utils/onedrive-picker-client';

import BookPicker from './BookPicker';
import type { ErrorInfo } from './FilePickerApp';
import JSTORPicker from './JSTORPicker';
import LMSFilePicker from './LMSFilePicker';
import URLPicker from './URLPicker';

type DialogType =
  | 'blackboardFile'
  | 'canvasFile'
  | 'd2lFile'
  | 'jstor'
  | 'url'
  | 'vitalSourceBook'
  | null;

export type ContentSelectorProps = {
  onError: (ei: ErrorInfo) => void;
  onSelectContent: (c: Content) => void;
  /** Used for testing */
  defaultActiveDialog?: DialogType;
};

/**
 * Component that allows the user to choose the content for an assignment.
 */
export default function ContentSelector({
  defaultActiveDialog = null,
  onError,
  onSelectContent,
}: ContentSelectorProps) {
  const {
    api: { authToken },
    filePicker: {
      blackboard: {
        enabled: blackboardFilesEnabled,
        listFiles: blackboardListFilesApi,
      },
      d2l: { enabled: d2lFilesEnabled, listFiles: d2lListFilesApi },
      canvas: { enabled: canvasFilesEnabled, listFiles: listFilesApi },
      google: {
        clientId: googleClientId,
        developerKey: googleDeveloperKey,
        origin: googleOrigin,
      },
      jstor: { enabled: jstorEnabled },
      microsoftOneDrive: {
        enabled: oneDriveFilesEnabled,
        clientId: oneDriveClientId,
        redirectURI: oneDriveRedirectURI,
      },
      vitalSource: { enabled: vitalSourceEnabled },
    },
  } = useConfig(['filePicker']);

  const [isLoadingIndicatorVisible, setLoadingIndicatorVisible] =
    useState(false);
  const [activeDialog, setActiveDialog] =
    useState<DialogType>(defaultActiveDialog);

  const cancelDialog = () => {
    setLoadingIndicatorVisible(false);
    setActiveDialog(null);
  };

  const selectDialog = (type: DialogType) => {
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
      // must provide the URL of the top-level frame to us, so we can pass it
      // to the Google Picker API. Otherwise, we can use the URL of the current
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

  const selectURL = (url: string) => {
    cancelDialog();
    onSelectContent({ type: 'url', url });
  };

  const selectCanvasFile = (file: File) => {
    cancelDialog();
    onSelectContent({ type: 'file', file });
  };

  const selectBlackboardFile = (file: File) => {
    cancelDialog();
    // file.id shall be a url of the form blackboard://content-resource/{file_id}
    onSelectContent({ type: 'url', url: file.id });
  };

  const selectD2LFile = (file: File) => {
    cancelDialog();
    // file.id shall be a url of the form d2l://content-resource/{file_id}
    onSelectContent({ type: 'url', url: file.id });
  };

  const selectVitalSourceBook = (book: Book, chapter: Chapter) => {
    cancelDialog();
    onSelectContent({
      type: 'url',
      url: chapter.url,
    });
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
    case 'd2lFile':
      dialog = (
        <LMSFilePicker
          authToken={authToken}
          listFilesApi={d2lListFilesApi}
          onCancel={cancelDialog}
          onSelectFile={selectD2LFile}
          missingFilesHelpLink={'https://web.hypothes.is/help-categories/d2l/'}
          withBreadcrumbs
        />
      );
      break;

    case 'jstor':
      dialog = <JSTORPicker onCancel={cancelDialog} onSelectURL={selectURL} />;
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
    setLoadingIndicatorVisible(true);
    try {
      const picker: GooglePickerClient = googlePicker!;
      const { id, name, url } = await picker.showPicker();
      await picker.enablePublicViewing(id);
      onSelectContent({ name, type: 'url', url });
    } catch (error) {
      if (!(error instanceof PickerCanceledError)) {
        console.error(error);
        onError({
          message: 'There was a problem choosing a file from Google Drive',
          error,
        });
      }
    } finally {
      setLoadingIndicatorVisible(false);
    }
  };

  const showOneDrivePicker = async () => {
    setLoadingIndicatorVisible(true);
    try {
      const picker: OneDrivePickerClient = oneDrivePicker!;
      const { name, url } = await picker.showPicker();
      onSelectContent({ name, type: 'url', url });
    } catch (error) {
      if (!(error instanceof PickerCanceledError)) {
        console.error(error);
        onError({
          message: 'There was a problem choosing a file from OneDrive',
          error,
        });
      }
    } finally {
      setLoadingIndicatorVisible(false);
    }
  };

  return (
    <>
      {isLoadingIndicatorVisible && <SpinnerOverlay />}
      <div className="flex flex-row p-y-2">
        <div className="flex flex-col space-y-1">
          <Button
            onClick={() => selectDialog('url')}
            variant="primary"
            data-testid="url-button"
          >
            Enter URL of web page or PDF
          </Button>
          {canvasFilesEnabled && (
            <Button
              onClick={() => selectDialog('canvasFile')}
              variant="primary"
              data-testid="canvas-file-button"
            >
              Select PDF from Canvas
            </Button>
          )}
          {blackboardFilesEnabled && (
            <Button
              onClick={() => selectDialog('blackboardFile')}
              variant="primary"
              data-testid="blackboard-file-button"
            >
              Select PDF from Blackboard
            </Button>
          )}
          {d2lFilesEnabled && (
            <Button
              onClick={() => selectDialog('d2lFile')}
              variant="primary"
              data-testid="d2l-file-button"
            >
              Select PDF from D2L
            </Button>
          )}
          {googlePicker && (
            <Button
              onClick={showGooglePicker}
              variant="primary"
              data-testid="google-drive-button"
            >
              Select PDF from Google Drive
            </Button>
          )}
          {jstorEnabled && (
            <Button
              onClick={() => selectDialog('jstor')}
              variant="primary"
              data-testid="jstor-button"
            >
              Select JSTOR article
            </Button>
          )}
          {oneDriveFilesEnabled && (
            <Button
              onClick={showOneDrivePicker}
              variant="primary"
              data-testid="onedrive-button"
            >
              Select PDF from OneDrive
            </Button>
          )}
          {vitalSourceEnabled && (
            <Button
              onClick={() => selectDialog('vitalSourceBook')}
              variant="primary"
              data-testid="vitalsource-button"
            >
              Select book from VitalSource
            </Button>
          )}
        </div>
        {/** This flex-grow element takes up remaining horizontal space so that
         * buttons don't span full width unecessarily.
         */}
        <div className="grow" />
      </div>
      <div>{dialog}</div>
    </>
  );
}
