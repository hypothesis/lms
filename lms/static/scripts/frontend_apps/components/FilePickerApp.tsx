import {
  Button,
  CardActions,
  SpinnerOverlay,
} from '@hypothesis/frontend-shared/lib/next';
import { useCallback, useEffect, useRef, useState } from 'preact/hooks';

import { useConfig } from '../config';
import { apiCall } from '../utils/api';
import type { Content, URLContent } from '../utils/content-item';
import { truncateURL } from '../utils/format';

import ContentSelector from './ContentSelector';
import ErrorModal from './ErrorModal';
import FilePickerFormFields from './FilePickerFormFields';
import GroupConfigSelector from './GroupConfigSelector';
import type { GroupConfig } from './GroupConfigSelector';

export type ErrorInfo = {
  message: string;
  error: Error;
};

export type FilePickerAppProps = {
  /** Callback invoked when the form is submitted */
  onSubmit?: () => void;
};
/**
 * For URL content, show the most meaningful explanation of the content we can
 * to the user. In cases where we have a filename (name), show that. For
 * Blackboard files, show a static string instead of the meaningless URL. Fall
 * back to showing a (truncated) URL.
 */
function formatContentURL(content: URLContent) {
  if (content.name) {
    return content.name;
  }

  if (content.url.startsWith('jstor://')) {
    return 'JSTOR article';
  }
  if (content.url.startsWith('blackboard://')) {
    return 'PDF file in Blackboard';
  }
  if (content.url.startsWith('d2l://')) {
    return 'PDF file in D2L';
  }
  if (content.url.startsWith('vitalsource://')) {
    return 'Book from VitalSource';
  }

  return truncateURL(content.url, 65 /* maxLength */);
}
/**
 * Return a human-readable description of assignment content.
 */
function contentDescription(content: Content) {
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
 */
export default function FilePickerApp({ onSubmit }: FilePickerAppProps) {
  const submitButton = useRef<HTMLInputElement | null>(null);
  const {
    api: { authToken },
    product: {
      settings: { groupsEnabled: enableGroupConfig },
    },
    filePicker: { deepLinkingAPI, formAction, formFields },
  } = useConfig(['filePicker']);

  const [content, setContent] = useState<Content | null>(null);

  const [groupConfig, setGroupConfig] = useState<GroupConfig>({
    useGroupSet: false,
    groupSet: null,
  });

  const [errorInfo, setErrorInfo] = useState<ErrorInfo | null>(null);

  /**
   * Flag indicating whether the form should be auto-submitted on the next
   * render.
   */
  const [shouldSubmit, setShouldSubmit] = useState(false);

  const [deepLinkingFields, setDeepLinkingFields] = useState<Record<
    string,
    string
  > | null>(null);

  const submit = useCallback(
    async (content: Content) => {
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
            group_set: groupConfig.useGroupSet ? groupConfig.groupSet : null,
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
      (!deepLinkingAPI || deepLinkingFields)
    ) {
      // Submit form using a hidden button rather than calling `form.submit()`
      // to facilitate observing the submission in tests and suppressing the
      // actual submit.
      submitButton.current!.click();
    }
  }, [shouldSubmit, deepLinkingAPI, deepLinkingFields]);

  const selectContent = useCallback(
    (content: Content) => {
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
        className="grid grid-cols-[auto_1fr] gap-4 w-[500px] max-w-[80vw] mx-auto mt-4"
        action={formAction}
        method="POST"
        onSubmit={onSubmit}
      >
        <h1 className="col-span-2 text-2xl font-bold">Assignment details</h1>
        <div className="text-end">
          <span className="font-bold">Assignment content</span>
        </div>
        <div className="space-y-3">
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
            <div className="text-end">
              <span className="font-bold">Group assignment</span>
            </div>
            <div>
              <GroupConfigSelector
                groupConfig={groupConfig}
                onChangeGroupConfig={setGroupConfig}
              />
            </div>
            <div className="col-span-2">
              <CardActions>
                <Button
                  disabled={groupConfig.useGroupSet && !groupConfig.groupSet}
                  variant="primary"
                  onClick={() => submit(content)}
                >
                  Continue
                </Button>
              </CardActions>
            </div>
          </>
        )}
        {content && (
          <FilePickerFormFields
            content={content}
            formFields={{ ...formFields, ...deepLinkingFields }}
            groupSet={groupConfig.useGroupSet ? groupConfig.groupSet : null}
          />
        )}
        <input style={{ display: 'none' }} ref={submitButton} type="submit" />
      </form>
      {shouldSubmit && <SpinnerOverlay />}
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
