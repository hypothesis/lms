import { createElement } from 'preact';
import { useContext, useEffect, useRef, useState } from 'preact/hooks';

import { Config } from '../config';

import ContentSelector from './ContentSelector';
import ErrorDialog from './ErrorDialog';
import FilePickerFormFields from './FilePickerFormFields';

/**
 * @typedef {import('../api-types').File} File
 * @typedef {import('../utils/content-item').Content} Content
 * @typedef {'lms'|'url'|null} DialogType
 *
 * @typedef FilePickerAppProps
 * @prop {DialogType} [defaultActiveDialog] -
 *   The dialog that should be shown when the app is first opened.
 * @prop {() => any} [onSubmit] - Callback invoked when the form is submitted.
 */

/**
 * An application that allows the user to choose the web page or PDF for an
 * assignment.
 *
 * @param {FilePickerAppProps} props
 */
export default function FilePickerApp({ onSubmit }) {
  const submitButton = useRef(/** @type {HTMLInputElement|null} */ (null));
  const {
    filePicker: {
      formAction,
      formFields,
      canvas: { ltiLaunchUrl },
    },
  } = useContext(Config);

  const [content, setContent] = useState(/** @type {Content|null} */ (null));

  /**
   * @typedef ErrorInfo
   * @prop {string} title
   * @prop {Error} error
   */

  const [errorInfo, setErrorInfo] = useState(
    /** @type {ErrorInfo|null} */ (null)
  );

  /**
   * Flag indicating whether the form should be auto-submitted on the next
   * render.
   */
  const [shouldSubmit, submit] = useState(false);

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

  /** @param {Content} content */
  const selectContent = content => {
    setContent(content);
    submit(true);
  };

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
        <ContentSelector
          onSelectContent={selectContent}
          onError={setErrorInfo}
        />
        {content && (
          <FilePickerFormFields
            ltiLaunchURL={ltiLaunchUrl}
            content={content}
            formFields={formFields}
          />
        )}
        {content && (
          <input
            name="document_url"
            type="hidden"
            value={content.file.id}
          />
        )}
        <input style={{ display: 'none' }} ref={submitButton} type="submit" />
      </form>
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
