import { FullScreenSpinner, LabeledButton } from '@hypothesis/frontend-shared';
import {
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'preact/hooks';

import { Config } from '../config';
import { apiCall } from '../utils/api';
import { truncateURL } from '../utils/format';

import ContentSelector from './ContentSelector';
import ErrorModal from './ErrorModal';
import FilePickerFormFields from './FilePickerFormFields';
import GroupConfigSelector from './GroupConfigSelector';

/**
 * @typedef {import('../api-types').File} File
 * @typedef {import('../utils/content-item').Content} Content
 * @typedef {import('../utils/content-item').URLContent} URLContent
 * @typedef {'lms'|'url'|null} DialogType
 *
 * @typedef {import('./GroupConfigSelector').GroupConfig} GroupConfig
 *
 * @typedef FilePickerAppProps
 * @prop {DialogType} [defaultActiveDialog] -
 *   The dialog that should be shown when the app is first opened.
 * @prop {() => void} [onSubmit] - Callback invoked when the form is submitted.
 */

/**
 * @typedef ErrorInfo
 * @prop {string} message
 * @prop {Error} error
 */

/**
 * For URL content, show the most meaningful explanation of the content we can
 * to the user. In cases where we have a filename (name), show that. For
 * Blackboard files, show a static string instead of the meaningless URL. Fall
 * back to showing a (truncated) URL.
 *
 * @param {URLContent} content
 * @returns {string}
 */
function formatContentURL(content) {
  if (content.name) {
    return content.name;
  }

  if (content.url.startsWith('jstor://')) {
    return 'JSTOR article';
  }
  if (content.url.startsWith('blackboard://')) {
    return 'PDF file in Blackboard';
  }
  if (content.url.startsWith('vitalsource://')) {
    return 'Book from VitalSource';
  }

  return truncateURL(content.url, 65 /* maxLength */);
}
/**
 * Return a human-readable description of assignment content.
 *
 * @param {Content} content - Type and details of assignment content
 * @return {string}
 */
function contentDescription(content) {
  switch (content.type) {
    case 'url':
      return formatContentURL(content);
    case 'file':
      return 'PDF file in Canvas';
    default:
      /* istanbul ignore next */
      throw new Error('Unknown content type');
  }
}

/**
 * An application that allows the user to choose the web page or PDF for an
 * assignment.
 *
 * @param {FilePickerAppProps} props
 */
export default function FilePickerApp({ onSubmit }) {
  const submitButton = /** @type {{ current: HTMLInputElement }} */ (useRef());
  const {
    api: { authToken },
    filePicker: {
      deepLinkingAPI,
      formAction,
      formFields,
      ltiLaunchUrl,
      blackboard,
      canvas,
    },
  } = useContext(Config);

  const [content, setContent] = useState(/** @type {Content|null} */ (null));

  const enableGroupConfig = blackboard?.groupsEnabled || canvas?.groupsEnabled;

  const [groupConfig, setGroupConfig] = useState(
    /** @type {GroupConfig} */ ({
      useGroupSet: false,
      groupSet: null,
    })
  );

  const [errorInfo, setErrorInfo] = useState(
    /** @type {ErrorInfo|null} */ (null)
  );

  /**
   * Flag indicating whether the form should be auto-submitted on the next
   * render.
   */
  const [shouldSubmit, setShouldSubmit] = useState(false);

  const [deepLinkingFields, setDeepLinkingFields] = useState(
    /** @type {Record<string,string>|null} */ (null)
  );

  const submit = useCallback(
    /** @param {Content} content */
    async content => {
      // Set shouldSubmit to true early to show the spinner while fetching form fields
      setShouldSubmit(true);

      if (!deepLinkingAPI || deepLinkingFields) {
        return;
      }

      // When deepLinkingAPI is present we want to call the backend to return the form
      // fields we'll forward to the LMS to complete the Deep Linking request
      try {
        const data = {
          ...deepLinkingAPI.data,
          content,
          extra_params: {
            groupSet: groupConfig.useGroupSet ? groupConfig.groupSet : null,
          },
        };
        setDeepLinkingFields(
          await apiCall({
            authToken: authToken,
            path: deepLinkingAPI.path,
            data,
          })
        );
      } catch (error) {
        setErrorInfo({
          message: 'Unable to configure assignment',
          error: error,
        });
        // Reset the state in case of an error allowing to start over
        setShouldSubmit(false);
        setContent(null);
      }
    },

    [
      authToken,
      deepLinkingFields,
      deepLinkingAPI,
      groupConfig.groupSet,
      groupConfig.useGroupSet,
    ]
  );

  // Submit the form after a selection is made via one of the available
  // methods.
  useEffect(() => {
    if (
      shouldSubmit &&
      // We either are not using the deepLinkingAPI, or if we are, wait for deepLinkingFields to be available
      (!deepLinkingAPI || (deepLinkingAPI && deepLinkingFields))
    ) {
      // Submit form using a hidden button rather than calling `form.submit()`
      // to facilitate observing the submission in tests and suppressing the
      // actual submit.
      submitButton.current.click();
    }
  }, [shouldSubmit, deepLinkingAPI, deepLinkingFields]);

  /** @type {(c: Content) => void} */
  const selectContent = useCallback(
    content => {
      setContent(content);
      if (!enableGroupConfig) {
        submit(content);
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
        <h1 className="FilePickerApp__heading text-2xl font-bold">
          Assignment details
        </h1>
        <div className="FilePickerApp__left-col">Assignment content</div>
        <div className="FilePickerApp__right-col">
          {content ? (
            <i data-testid="content-summary" style="break-all">
              {contentDescription(content)}
            </i>
          ) : (
            <>
              <p>
                You can select content for your assignment from one of the
                following sources:
              </p>
              <ContentSelector
                onSelectContent={selectContent}
                onError={setErrorInfo}
              />
            </>
          )}
        </div>
        {content && enableGroupConfig && (
          <>
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
                onClick={() => submit(content)}
              >
                Continue
              </LabeledButton>
            </div>
          </>
        )}
        {content && (
          <FilePickerFormFields
            ltiLaunchURL={ltiLaunchUrl}
            content={content}
            formFields={{ ...formFields, ...deepLinkingFields }}
            groupSet={groupConfig.useGroupSet ? groupConfig.groupSet : null}
          />
        )}
        <input style={{ display: 'none' }} ref={submitButton} type="submit" />
      </form>
      {shouldSubmit && <FullScreenSpinner />}
      {errorInfo && (
        <ErrorModal
          description={errorInfo.message}
          error={errorInfo.error}
          onCancel={() => setErrorInfo(null)}
        />
      )}
    </main>
  );
}
