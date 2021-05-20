import { LabeledButton } from '@hypothesis/frontend-shared';
import { createElement } from 'preact';
import { useContext, useEffect, useMemo, useRef, useState } from 'preact/hooks';

import { Config } from '../config';
import {
  GooglePickerClient,
  PickerCanceledError,
} from '../utils/google-picker-client';

import ErrorDialog from './ErrorDialog';
import FilePickerFormFields from './FilePickerFormFields';
import LMSFilePicker from './LMSFilePicker';
import Spinner from './Spinner';
import URLPicker from './URLPicker';

/**
 * @typedef {import('../api-types').File} File
 * @typedef {'lms'|'url'|null} DialogType
 *
 * @typedef FilePickerAppProps
 * @prop {DialogType} [defaultActiveDialog] -
 *   The dialog that should be shown when the app is first opened.
 * @prop {() => any} [onSubmit] - Callback invoked when the form is submitted.
 */

/**
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
 * @prop {string} bookID
 * @prop {string} cfi
 *
 * @typedef {FileContent|URLContent|VitalSourceBookContent} Content
 */

/**
 * An application that allows the user to choose the web page or PDF for an
 * assignment.
 *
 * @param {FilePickerAppProps} props
 */
export default function FilePickerApp({
  defaultActiveDialog = null,
  onSubmit,
}) {
  const submitButton = useRef(/** @type {HTMLInputElement|null} */ (null));
  const {
    api: { authToken },
    filePicker: {
      formAction,
      formFields,
      canvas: { enabled: canvasEnabled, listFiles: listFilesApi, ltiLaunchUrl },
      google: {
        clientId: googleClientId,
        developerKey: googleDeveloperKey,
        origin: googleOrigin,
      },
      vitalSource: { enabled: vitalSourceEnabled },
    },
  } = useContext(Config);

  const [activeDialog, setActiveDialog] = useState(defaultActiveDialog);
  const [content, setContent] = useState(/** @type {Content|null} */ (null));

  const [isLoadingIndicatorVisible, setLoadingIndicatorVisible] =
    useState(false);

  /**
   * @typedef ErrorInfo
   * @prop {string} title
   * @prop {Error} error
   */

  const [errorInfo, setErrorInfo] = useState(
    /** @type {ErrorInfo|null} */ (null)
  );

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

  /**
   * Flag indicating whether the form should be auto-submitted on the next
   * render.
   */
  const [shouldSubmit, submit] = useState(false);

  const cancelDialog = () => {
    setLoadingIndicatorVisible(false);
    setActiveDialog(null);
  };

  /** @param {DialogType} type */
  const selectDialog = type => {
    setLoadingIndicatorVisible(true);
    setActiveDialog(type);
  };

  /** @param {File} file */
  const selectLMSFile = file => {
    cancelDialog();
    setContent({ type: 'file', file });
    submit(true);
  };

  /** @param {string} url */
  const selectURL = url => {
    cancelDialog();
    setContent({ type: 'url', url });
    submit(true);
  };

  const showGooglePicker = async () => {
    try {
      setLoadingIndicatorVisible(true);
      const picker = /** @type {GooglePickerClient} */ (googlePicker);
      const { id, url } = await picker.showPicker();
      await picker.enablePublicViewing(id);
      setContent({ type: 'url', url });
      submit(true);
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
    // Chosen from `https://api.vitalsource.com/v4/products` response.
    const bookID = 'BOOKSHELF-TUTORIAL';
    // CFI chosen from `https://api.vitalsource.com/v4/products/BOOKSHELF-TUTORIAL/toc`
    // response.
    const cfi = '/6/8[;vnd.vst.idref=vst-70a6f9d3-0932-45ba-a583-6060eab3e536]';

    setContent({ type: 'vitalsource', bookID, cfi });
    submit(true);
  };

  // Submit the form after a selection is made via one of the available
  // methods.
  useEffect(() => {
    if (shouldSubmit) {
      // Submit form using a hidden button rather than calling `form.submit()`
      // to facilitate observing the submission in tests and suppressing the
      // actual submit.
      submitButton.current.click();
    }
  }, [shouldSubmit]);

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

  return (
    <main>
      <form
        className="FilePickerApp__form"
        action={formAction}
        method="POST"
        onSubmit={onSubmit}
      >
        <h1 className="heading-1">Select web page or PDF</h1>
        <p>
          You can select content for your assignment from one of the following
          sources:
        </p>
        {content?.type === 'url' && (
          // Set the `document_url` form field which is used by the `configure_module_item`
          // view. Used in LMSes where assignments are configured on first launch.
          <input name="document_url" type="hidden" value={content.url} />
        )}
        <div className="FilePickerApp__actions">
          <div className="FilePickerApp__actions-buttons">
            <LabeledButton
              variant="primary"
              onClick={() => selectDialog('url')}
              data-testid="url-button"
            >
              Enter URL of web page or PDF
            </LabeledButton>
            {canvasEnabled && (
              <LabeledButton
                variant="primary"
                onClick={() => selectDialog('lms')}
                data-testid="pdf-button"
              >
                Select PDF from Canvas
              </LabeledButton>
            )}
            {googlePicker && (
              <LabeledButton
                variant="primary"
                onClick={showGooglePicker}
                data-testid="drive-button"
              >
                Select PDF from Google Drive
              </LabeledButton>
            )}
            {vitalSourceEnabled && (
              <LabeledButton
                variant="primary"
                onClick={selectVitalSourceBook}
                data-testid="vitalsource-button"
              >
                Select book from VitalSource
              </LabeledButton>
            )}
          </div>
          <div className="u-stretch" />
        </div>
        {content && (
          <FilePickerFormFields
            ltiLaunchURL={ltiLaunchUrl}
            content={content}
            formFields={formFields}
          />
        )}
        <input style={{ display: 'none' }} ref={submitButton} type="submit" />
      </form>
      {isLoadingIndicatorVisible && (
        <div className="FilePickerApp__loading-backdrop">
          <Spinner className="FilePickerApp__loading-spinner" />
        </div>
      )}
      {dialog}
      {errorInfo && (
        <ErrorDialog
          title={errorInfo.title}
          error={errorInfo.error}
          onCancel={() => setErrorInfo(null)}
        />
      )}
    </main>
  );
}
