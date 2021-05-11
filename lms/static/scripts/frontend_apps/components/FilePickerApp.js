import { LabeledButton } from '@hypothesis/frontend-shared';
import { Fragment, createElement } from 'preact';
import { useContext, useEffect, useRef, useState } from 'preact/hooks';

import { Config } from '../config';

import ContentSelector from './ContentSelector';
import ErrorDialog from './ErrorDialog';
import GroupConfigSelector from './GroupConfigSelector';
import LTIContentItemFormFields from './LTIContentItemFormFields';

/**
 * @typedef {import('../api-types').File} File
 * @typedef {import('./ContentSelector').Content} Content
 * @typedef {import('./GroupConfigSelector').GroupConfig} GroupConfig
 *
 * @typedef FilePickerAppProps
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
      canvas: { groupsEnabled, ltiLaunchUrl },
    },
  } = useContext(Config);

  const [content, setContent] = useState(/** @type {Content|null} */ (null));
  const [groupConfig, setGroupConfig] = useState(
    /** @type {GroupConfig} */ ({ useGroups: false, groupSet: null })
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
  const submit = () => setShouldSubmit(true);

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

  return (
    <main>
      <form
        className="FilePickerApp__form"
        action={formAction}
        method="POST"
        onSubmit={onSubmit}
      >
        {!content && (
          <Fragment>
            <h1 className="heading-1">Select web page or PDF</h1>
            <p>
              You can select content for your assignment from one of the
              following sources:
            </p>
            <ContentSelector
              setErrorInfo={setErrorInfo}
              onSelectContent={content => {
                setContent(content);
                if (!groupsEnabled) {
                  submit();
                }
              }}
            />
          </Fragment>
        )}
        {content && groupsEnabled && (
          <Fragment>
            <GroupConfigSelector
              groupConfig={groupConfig}
              onChangeGroupConfig={setGroupConfig}
            />
            <LabeledButton
              disabled={groupConfig.useGroups && !groupConfig.groupSet}
              onClick={() => submit()}
              variant="primary"
            >
              Continue
            </LabeledButton>
          </Fragment>
        )}
        {content && (
          <LTIContentItemFormFields
            content={content}
            formFields={formFields}
            grouping={groupConfig}
            ltiLaunchURL={ltiLaunchUrl}
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
