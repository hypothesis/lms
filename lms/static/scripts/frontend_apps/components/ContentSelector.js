import { Fragment, createElement } from 'preact';
import { useContext, useMemo, useState } from 'preact/hooks';

import { LabeledButton } from '@hypothesis/frontend-shared';

import { Config } from '../config';
import {
  GooglePickerClient,
  PickerCanceledError,
} from '../utils/google-picker-client';
import LMSFilePicker from './LMSFilePicker';
import URLPicker from './URLPicker';
import Spinner from './Spinner';

/**
 * @typedef {import('../api-types').File} File
 *
 * @typedef ErrorInfo
 * @prop {string} title
 * @prop {Error} error
 *
 * @typedef {'lms'|'url'|null} DialogType
 *
 * @typedef FileContent
 * @prop {'file'} type
 * @prop {File} file
 *
 * @typedef URLContent
 * @prop {'url'} type
 * @prop {string} url
 *
 * @typedef VitalSourceBookContent
 * @prop {'vitalsource'} type
 *
 * @typedef {FileContent|URLContent|VitalSourceBookContent} Content
 */

/**
 * @typedef ContentSelectorProps
 * @prop {(ei: ErrorInfo) => void} setErrorInfo
 * @prop {(c: Content) => void} onSelectContent
 */

/**
 * Component that allows the user to choose the content for an assignment.
 *
 * @param {ContentSelectorProps} props
 */
export default function ContentSelector({ setErrorInfo, onSelectContent }) {
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

  const [isLoadingIndicatorVisible, setLoadingIndicatorVisible] = useState(
    false
  );
  const [activeDialog, setActiveDialog] = useState(
    /** @type {DialogType} */ (null)
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
    case 'lms':
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
        setErrorInfo({
          title: 'There was a problem choosing a file from Google Drive',
          error,
        });
      }
    }
  };

  const selectVitalSourceBook = () => {
    onSelectContent({ type: 'vitalsource' });
  };

  return (
    <Fragment>
      {isLoadingIndicatorVisible && (
        <div className="FilePickerApp__loading-backdrop">
          <Spinner className="FilePickerApp__loading-spinner" />
        </div>
      )}
      <div className="FilePickerApp__document-source-buttons">
        <LabeledButton
          onClick={() => selectDialog('url')}
          type="button"
          variant="primary"
        >
          Enter URL of web page or PDF
        </LabeledButton>
        {canvasEnabled && (
          <LabeledButton
            onClick={() => selectDialog('lms')}
            variant="primary"
          >
            Select PDF from Canvas
          </LabeledButton>
        )}
        {googlePicker && (
          <LabeledButton
            onClick={showGooglePicker}
            variant="primary"
          >
            Select PDF from Google Drive
          </LabeledButton>
        )}
        {vitalSourceEnabled && (
          <LabeledButton
            onClick={selectVitalSourceBook}
            variant="primary"
          >
            Select book from VitalSource
          </LabeledButton>
        )}
      </div>
      {dialog}
    </Fragment>
  );
}
