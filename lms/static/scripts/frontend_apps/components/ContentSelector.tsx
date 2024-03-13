import { OptionButton, SpinnerOverlay } from '@hypothesis/frontend-shared';
import { useMemo, useState } from 'preact/hooks';

import type { File, Page } from '../api-types';
import { useConfig } from '../config';
import { PickerCanceledError } from '../errors';
import type { Content } from '../utils/content-item';
import { GooglePickerClient } from '../utils/google-picker-client';
import { OneDrivePickerClient } from '../utils/onedrive-picker-client';
import { isYouTubeURL } from '../utils/youtube';
import BookPicker from './BookPicker';
import type { ErrorInfo } from './FilePickerApp';
import JSTORPicker from './JSTORPicker';
import LMSFilePicker from './LMSFilePicker';
import URLPicker from './URLPicker';
import YouTubePicker from './YouTubePicker';

type DialogType =
  | 'blackboardFile'
  | 'canvasFile'
  | 'canvasPage'
  | 'canvasStudio'
  | 'd2lFile'
  | 'moodleFile'
  | 'moodlePage'
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
      moodle: {
        enabled: moodleFilesEnabled,
        listFiles: moodleListFilesApi,
        pagesEnabled: moodlePagesEnabled,
        listPages: moodleListPagesApi,
      },
      canvas: {
        enabled: canvasFilesEnabled,
        listFiles: listFilesApi,
        foldersEnabled: canvasWithFolders,
        pagesEnabled: canvasPagesEnabled,
        listPages: listPagesApi,
      },
      canvasStudio: {
        enabled: canvasStudioEnabled,
        listMedia: listCanvasStudioMediaApi,
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
      vitalSource: {
        enabled: vitalSourceEnabled,
        pageRangesEnabled: vitalSourcePageRangesEnabled,
      },
      youtube: { enabled: youtubeEnabled },
    },
  } = useConfig(['api', 'filePicker']);

  // Map the existing content selection to a dialog type and value. We don't
  // open the corresponding dialog immediately, but do pre-fill the dialog
  // in some cases if the user does open it.
  const [initialType, initialValue] = useMemo(
    () =>
      initialContent ? extractContentTypeAndValue(initialContent) : [null, ''],
    [initialContent],
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

  const selectURL = (url: string, name?: string) => {
    cancelDialog();
    onSelectContent({ type: 'url', url, name });
  };

  // file.id is a URL with a `blackboard://`, `d2l://` or `moodle://` prefix.
  const selectFileAsURL = (file: File | Page) => selectURL(file.id);

  const selectPageAsURL = (page: File | Page, lms: string) => {
    const name = `${lms} page: ${page.display_name}`;
    selectURL(page.id, name);
  };

  const selectCanvasFile = (file: File | Page) => {
    cancelDialog();
    onSelectContent({ type: 'file', file: file as File });
  };

  const selectYouTubeURL = (url: string, title?: string) => {
    const name = title && `YouTube: ${title}`;
    selectURL(url, name);
  };

  const selectCanvasPage = (page: File | Page) =>
    selectPageAsURL(page, 'Canvas');

  const selectCanvasStudio = (video: File | Page) => {
    const name = `Canvas Studio video: ${video.display_name}`;
    selectURL(video.id, name);
  };

  const selectMoodlePage = (page: File | Page) =>
    selectPageAsURL(page, 'Moodle');

  const selectVitalSourceBook = async (
    selection: unknown,
    documentURL: string,
  ) => selectURL(documentURL);

  const getDefaultValue = (type: DialogType) =>
    type === initialType ? initialValue : undefined;

  const getDefaultValueIfYouTubeURL = () => {
    const url = getDefaultValue('url');
    return url && isYouTubeURL(url) ? url : undefined;
  };

  let dialog;
  switch (activeDialog) {
    case 'url':
      dialog = (
        <URLPicker
          defaultURL={getDefaultValue('url')}
          onCancel={cancelDialog}
          onSelectURL={selectURL}
          youtubeEnabled={youtubeEnabled}
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
    case 'canvasPage':
      dialog = (
        <LMSFilePicker
          authToken={authToken}
          listFilesApi={listPagesApi}
          onCancel={cancelDialog}
          onSelectFile={selectCanvasPage}
          missingFilesHelpLink="https://community.canvaslms.com/t5/Instructor-Guide/How-do-I-create-a-new-page-in-a-course/ta-p/1031"
          documentType="page"
        />
      );
      break;
    case 'canvasStudio':
      dialog = (
        <LMSFilePicker
          authToken={authToken}
          listFilesApi={listCanvasStudioMediaApi}
          onCancel={cancelDialog}
          onSelectFile={selectCanvasStudio}
          missingFilesHelpLink="https://community.canvaslms.com/t5/Canvas-Studio-Guide/How-do-I-use-Canvas-Studio/ta-p/1678"
          documentType="video"
        />
      );
      break;
    case 'blackboardFile':
      dialog = (
        <LMSFilePicker
          authToken={authToken}
          listFilesApi={blackboardListFilesApi}
          onCancel={cancelDialog}
          onSelectFile={selectFileAsURL}
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
          onSelectFile={selectFileAsURL}
          missingFilesHelpLink={
            'https://web.hypothes.is/help/using-hypothesis-with-d2l-course-content-files/'
          }
          withBreadcrumbs
        />
      );
      break;
    case 'moodleFile':
      dialog = (
        <LMSFilePicker
          authToken={authToken}
          listFilesApi={moodleListFilesApi}
          onCancel={cancelDialog}
          onSelectFile={selectFileAsURL}
          missingFilesHelpLink={'https://web.hypothes.is/help/'}
          withBreadcrumbs
        />
      );
      break;

    case 'moodlePage':
      dialog = (
        <LMSFilePicker
          authToken={authToken}
          listFilesApi={moodleListPagesApi}
          onCancel={cancelDialog}
          onSelectFile={selectMoodlePage}
          missingFilesHelpLink={'https://web.hypothes.is/help/'}
          documentType="page"
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
          allowPageRangeSelection={vitalSourcePageRangesEnabled}
          onCancel={cancelDialog}
          onSelectBook={selectVitalSourceBook}
        />
      );
      break;
    case 'youtube':
      dialog = (
        <YouTubePicker
          defaultURL={getDefaultValueIfYouTubeURL()}
          onCancel={cancelDialog}
          onSelectURL={selectYouTubeURL}
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
      selectURL(url, name);
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
      selectURL(url, name);
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
      <div className="grid grid-cols-2 gap-y-2 gap-x-3 max-w-[28rem]">
        <OptionButton
          data-testid="url-button"
          details="Web page | PDF"
          onClick={() => selectDialog('url')}
          title="Enter a URL to a web page or PDF"
        >
          URL
        </OptionButton>
        {canvasFilesEnabled && (
          <OptionButton
            data-testid="canvas-file-button"
            details="PDF"
            onClick={() => selectDialog('canvasFile')}
            title="Select PDF from Canvas"
          >
            Canvas File
          </OptionButton>
        )}
        {canvasPagesEnabled && (
          <OptionButton
            data-testid="canvas-page-button"
            details="Page"
            onClick={() => selectDialog('canvasPage')}
            title="Select a Page from Canvas"
          >
            Canvas Page
          </OptionButton>
        )}
        {canvasStudioEnabled && (
          <OptionButton
            data-testid="canvas-studio-button"
            details="Video"
            onClick={() => selectDialog('canvasStudio')}
          >
            Canvas Studio
          </OptionButton>
        )}
        {blackboardFilesEnabled && (
          <OptionButton
            data-testid="blackboard-file-button"
            details="PDF"
            onClick={() => selectDialog('blackboardFile')}
            title="Select PDF from Blackboard"
          >
            Blackboard
          </OptionButton>
        )}
        {d2lFilesEnabled && (
          <OptionButton
            data-testid="d2l-file-button"
            details="PDF"
            onClick={() => selectDialog('d2lFile')}
            title="Select PDF from D2L"
          >
            D2L
          </OptionButton>
        )}
        {moodleFilesEnabled && (
          <OptionButton
            data-testid="moodle-file-button"
            details="PDF"
            onClick={() => selectDialog('moodleFile')}
            title="Select PDF from Moodle"
          >
            Moodle File
          </OptionButton>
        )}
        {moodlePagesEnabled && (
          <OptionButton
            data-testid="moodle-page-button"
            details="Page"
            onClick={() => selectDialog('moodlePage')}
            title="Select a Page from Moodle"
          >
            Moodle Page
          </OptionButton>
        )}

        {googlePicker && (
          <OptionButton
            details="PDF"
            data-testid="google-drive-button"
            onClick={showGooglePicker}
            title="Select PDF from Google Drive"
          >
            Google Drive
          </OptionButton>
        )}
        {jstorEnabled && (
          <OptionButton
            data-testid="jstor-button"
            details="Article"
            onClick={() => selectDialog('jstor')}
            title="Select JSTOR article"
          >
            JSTOR
          </OptionButton>
        )}
        {oneDriveFilesEnabled && (
          <OptionButton
            data-testid="onedrive-button"
            details="PDF"
            onClick={showOneDrivePicker}
            title="Select PDF from OneDrive"
          >
            OneDrive
          </OptionButton>
        )}
        {vitalSourceEnabled && (
          <OptionButton
            data-testid="vitalsource-button"
            details="Book"
            onClick={() => selectDialog('vitalSourceBook')}
            title="Select book from VitalSource"
          >
            VitalSource
          </OptionButton>
        )}
        {youtubeEnabled && (
          <OptionButton
            data-testid="youtube-button"
            details="Video"
            onClick={() => selectDialog('youtube')}
            title="Select video from YouTube"
          >
            YouTube
          </OptionButton>
        )}
      </div>

      <div>{dialog}</div>
    </>
  );
}
