import { LabeledButton } from '@hypothesis/frontend-shared';
import { Fragment, createElement } from 'preact';
import { useContext, useMemo, useState } from 'preact/hooks';

import { Config } from '../config';
import {
  GooglePickerClient,
  PickerCanceledError,
} from '../utils/google-picker-client';
import LMSFilePicker from './LMSFilePicker';
import Spinner from './Spinner';
import URLPicker from './URLPicker';

/**
 * @typedef {import('../api-types').File} File
 *
 * @typedef ErrorInfo
 * @prop {string} title
 * @prop {Error} error
 *
 * @typedef {'lmsFile'|'url'|null} DialogType
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
      canvas: { enabled: canvasEnabled, listFiles: listFilesApi },
      google: {
        clientId: googleClientId,
        developerKey: googleDeveloperKey,
        origin: googleOrigin,
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
    setLoadingIndicatorVisible(true);
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

  /** @param {string} url */
  const selectURL = url => {
    cancelDialog();
    onSelectContent({ type: 'url', url });
  };

  /** @param {File} file */
  const selectLMSFile = file => {
    cancelDialog();
    onSelectContent({ type: 'file', file });
  };

  let dialog;
  switch (activeDialog) {
    case 'url':
      dialog = <URLPicker onCancel={cancelDialog} onSelectURL={selectURL} />;
      break;
    case 'lmsFile':
      dialog = (
        <LMSFilePicker
          authToken={authToken}
          listFilesApi={listFilesApi}
          onCancel={cancelDialog}
          onSelectFile={selectLMSFile}
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

  const selectVitalSourceBook = () => {
    // Chosen from `https://api.vitalsource.com/v4/products` response.
    const bookID = 'BOOKSHELF-TUTORIAL';
    // CFI chosen from `https://api.vitalsource.com/v4/products/BOOKSHELF-TUTORIAL/toc`
    // response.
    const cfi = '/6/8[;vnd.vst.idref=vst-70a6f9d3-0932-45ba-a583-6060eab3e536]';

    onSelectContent({ type: 'vitalsource', bookID, cfi });
  };

  return (
    <Fragment>
      {isLoadingIndicatorVisible && (
        <div className="ContentSelector__loading-backdrop">
          <Spinner className="ContentSelector__loading-spinner" />
        </div>
      )}
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
          {canvasEnabled && (
            <LabeledButton
              onClick={() => selectDialog('lmsFile')}
              variant="primary"
              data-testid="lms-file-button"
            >
              Select PDF from Canvas
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
          {vitalSourceEnabled && (
            <LabeledButton
              onClick={selectVitalSourceBook}
              variant="primary"
              data-testid="vitalsource-button"
            >
              Select book from VitalSource
            </LabeledButton>
          )}
        </div>
        <div className="u-stretch" />
      </div>
      {dialog}
    </Fragment>
  );
}
