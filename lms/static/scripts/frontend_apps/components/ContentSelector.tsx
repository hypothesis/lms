import { Button, SpinnerOverlay } from '@hypothesis/frontend-shared';
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
import YouTubePicker from './YouTubePicker';

type DialogType =
  | 'blackboardFile'
  | 'canvasFile'
  | 'd2lFile'
  | 'jstor'
  | 'url'
  | 'vitalSourceBook'
  | 'youtube'
  | null;

export type ContentSelectorProps = {
  initialContent?: Content;

  onError: (ei: ErrorInfo) => void;
  onSelectContent: (c: Content) => void;

  /** Used for testing */
  defaultActiveDialog?: DialogType;
};

function extractContentTypeAndValue(content: Content): [DialogType, string] {
  if (content.type === 'url' && content.url.match(/^https?:/i)) {
    return ['url', content.url];
  } else if (content.type === 'url' && content.url.startsWith('jstor:')) {
    return ['jstor', content.url.slice('jstor://'.length)];
  } else {
    // Other content types are not currently handled, which means that the user
    // will need to select content starting from a blank state, as opposed to
    // being able to adjust the selection.
    return [null, ''];
  }
}

/**
 * Component that allows the user to choose the content for an assignment.
 */
export default function ContentSelector({
  initialContent,
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
      canvas: {
        enabled: canvasFilesEnabled,
        listFiles: listFilesApi,
        foldersEnabled: canvasWithFolders,
      },
      google: {
        enabled: googleDriveEnabled,
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
      youtube: { enabled: youtubeEnabled },
    },
  } = useConfig(['filePicker']);

  // Map the existing content selection to a dialog type and value. We don't
  // open the corresponding dialog immediately, but do pre-fill the dialog
  // in some cases if the user does open it.
  const [initialType, initialValue] = useMemo(
    () =>
      initialContent ? extractContentTypeAndValue(initialContent) : [null, ''],
    [initialContent]
  );

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
    if (
      !googleDriveEnabled ||
      !googleClientId ||
      !googleDeveloperKey ||
      !googleOrigin
    ) {
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
  }, [googleDriveEnabled, googleDeveloperKey, googleClientId, googleOrigin]);

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
    // file.id is a URL with a `blackboard://` prefix.
    onSelectContent({ type: 'url', url: file.id });
  };

  const selectD2LFile = (file: File) => {
    cancelDialog();
    // file.id is a URL with a `d2l://` prefix.
    onSelectContent({ type: 'url', url: file.id });
  };

  const selectVitalSourceBook = (book: Book, chapter: Chapter) => {
    cancelDialog();
    onSelectContent({
      type: 'url',
      url: chapter.url,
    });
  };

  const getDefaultValue = (type: DialogType) =>
    type === initialType ? initialValue : undefined;

  let dialog;
  switch (activeDialog) {
    case 'url':
      dialog = (
        <URLPicker
          defaultURL={getDefaultValue('url')}
          onCancel={cancelDialog}
          onSelectURL={selectURL}
        />
      );
      break;
    case 'canvasFile':
      dialog = (
        <LMSFilePicker
          authToken={authToken}
          listFilesApi={listFilesApi}
          onCancel={cancelDialog}
          onSelectFile={selectCanvasFile}
          missingFilesHelpLink="https://community.canvaslms.com/t5/Instructor-Guide/How-do-I-upload-a-file-to-a-course/ta-p/618"
          withBreadcrumbs={canvasWithFolders}
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
          missingFilesHelpLink={
            'https://web.hypothes.is/help/using-hypothesis-with-d2l-course-content-files/'
          }
          withBreadcrumbs
        />
      );
      break;

    case 'jstor':
      dialog = (
        <JSTORPicker
          defaultArticle={getDefaultValue('jstor')}
          onCancel={cancelDialog}
          onSelectURL={selectURL}
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
    case 'youtube':
      dialog = <YouTubePicker onCancel={cancelDialog} onSelectURL={() => {}} />;
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
          {youtubeEnabled && (
            <Button
              onClick={() => selectDialog('youtube')}
              variant="primary"
              data-testid="youtube-button"
            >
              Select video from YouTube
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
