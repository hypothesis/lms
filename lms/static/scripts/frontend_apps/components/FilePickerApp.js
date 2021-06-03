import { LabeledButton } from '@hypothesis/frontend-shared';
import { Fragment, createElement } from 'preact';
import {
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'preact/hooks';

import { Config } from '../config';

import ContentSelector from './ContentSelector';
import ErrorDialog from './ErrorDialog';
import FilePickerFormFields from './FilePickerFormFields';
import GroupConfigSelector from './GroupConfigSelector';

/**
 * @typedef {import('../api-types').File} File
 * @typedef {import('../utils/content-item').Content} Content
 * @typedef {'lms'|'url'|null} DialogType
 *
 * @typedef {import('./GroupConfigSelector').GroupConfig} GroupConfig
 *
 * @typedef FilePickerAppProps
 * @prop {DialogType} [defaultActiveDialog] -
 *   The dialog that should be shown when the app is first opened.
 * @prop {() => any} [onSubmit] - Callback invoked when the form is submitted.
 */

/**
 * Return a human-readable description of assignment content.
 *
 * @param {Content} content - Type and details of assignment content
 * @return {string}
 */
function contentDescription(content) {
  switch (content.type) {
    case 'url':
      return content.url;
    case 'file':
      return 'PDF file in Canvas';
    case 'vitalsource':
      return 'Book from VitalSource';
    default:
      return 'Other content';
  }
}

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
      canvas: { groupsEnabled: enableGroupConfig, ltiLaunchUrl },
    },
  } = useContext(Config);

  const [content, setContent] = useState(/** @type {Content|null} */ (null));

  const [groupConfig, setGroupConfig] = useState(
    /** @type {GroupConfig} */ ({
      useGroupSet: false,
      groupSet: null,
    })
  );

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
  const [shouldSubmit, setShouldSubmit] = useState(false);
  const submit = useCallback(() => setShouldSubmit(true), []);

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

  /** @type {(c: Content) => void} */
  const selectContent = useCallback(
    content => {
      setContent(content);
      if (!enableGroupConfig) {
        submit();
      }
    },
    [enableGroupConfig, submit]
  );

  return (
    <main>
      <form
        className="FilePickerApp__form"
        action={formAction}
        method="POST"
        onSubmit={onSubmit}
      >
        <h1 className="FilePickerApp__heading">Assignment details</h1>
        <div className="FilePickerApp__left-col">Assignment content</div>
        <div className="FilePickerApp__right-col">
          {content ? (
            <i>{contentDescription(content)}</i>
          ) : (
            <Fragment>
              <p>
                You can select content for your assignment from one of the
                following sources:
              </p>
              <ContentSelector
                onSelectContent={selectContent}
                onError={setErrorInfo}
              />
            </Fragment>
          )}
        </div>
        {content && enableGroupConfig && (
          <Fragment>
            <div className="FilePickerApp__left-col">Group assignment</div>
            <div className="FilePickerApp__right-col">
              <GroupConfigSelector
                groupConfig={groupConfig}
                onChangeGroupConfig={setGroupConfig}
              />
            </div>
            <div className="FilePickerApp__footer">
              <LabeledButton
                disabled={groupConfig.useGroupSet && !groupConfig.groupSet}
                variant="primary"
                onClick={submit}
              >
                Continue
              </LabeledButton>
            </div>
          </Fragment>
        )}
        {content && (
          <FilePickerFormFields
            ltiLaunchURL={ltiLaunchUrl}
            content={content}
            formFields={formFields}
            groupSet={groupConfig.useGroupSet ? groupConfig.groupSet : null}
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
