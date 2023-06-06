import {
  ArrowLeftIcon,
  Button,
  Card,
  CardActions,
  CardContent,
  CardHeader,
  Link,
  LinkButton,
  Scroll,
  SpinnerOverlay,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { ComponentChildren } from 'preact';
import { useCallback, useEffect, useRef, useState } from 'preact/hooks';
import { Link as RouterLink } from 'wouter-preact';

import { useConfig } from '../config';
import type { ConfigObject } from '../config';
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

/* A step or 'screen' of the assignment configuration */
type PickerStep = 'content-selection' | 'group-configuration';

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

  return truncateURL(content.url, 50 /* maxLength */);
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

function contentFromURL(url: string): Content {
  return { type: 'url', url };
}

/**
 * Fetch additional configuration needed by the file picker app.
 *
 * This is needed when transitioning to the file picker from another route.
 *
 * Returns the result of merging {@link config} with the configuration for
 * the file picker app.
 */
export async function loadFilePickerConfig(
  config: ConfigObject
): Promise<ConfigObject> {
  if (!config.editing) {
    throw new Error('Assignment editing config missing');
  }

  const authToken = config.api.authToken;
  const { path, data } = config.editing.getConfig;
  const { assignment, filePicker } = await apiCall<Partial<ConfigObject>>({
    authToken,
    path,
    data,
  });

  return {
    ...config,
    assignment,
    filePicker,
  };
}

/**
 * Render a label for a step in the configuration. Any provided `description`
 * will only render if this label's associated `step` is the `currentStep`.
 */
function PanelLabel({
  children,
  description,
  isCurrentStep,
}: {
  children: ComponentChildren;
  description?: ComponentChildren;
  isCurrentStep: boolean;
}) {
  return (
    <div className="space-y-1.5 leading-none">
      <div className="sm:text-end font-medium text-slate-600 uppercase">
        {children}
      </div>
      {isCurrentStep && (
        <div className="sm:text-end font-normal text-stone-500">
          {description}
        </div>
      )}
    </div>
  );
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
    assignment,
    filePicker: { deepLinkingAPI, formAction, formFields },
  } = useConfig(['filePicker']);

  // Currently selected content for assignment.
  const [content, setContent] = useState<Content | null>(
    assignment ? contentFromURL(assignment.document.url) : null
  );

  // Flag indicating if we are editing content that was previously selected.
  const [editingContent, setEditingContent] = useState(false);
  // True if we are editing an existing assignment configuration.
  const isEditing = !!assignment;

  let currentStep: PickerStep;
  if (editingContent) {
    currentStep = 'content-selection';
  } else if (isEditing) {
    currentStep = 'group-configuration';
  } else {
    currentStep =
      content && enableGroupConfig
        ? 'group-configuration'
        : 'content-selection';
  }

  const [groupConfig, setGroupConfig] = useState<GroupConfig>({
    useGroupSet: !!assignment?.group_set_id,
    groupSet: assignment?.group_set_id ?? null,
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
      setEditingContent(false);

      // If this is a new assignment and the only choice the user has to make
      // is the content, we submit as soon as they select the content.
      if (!isEditing && !enableGroupConfig) {
        submit(content);
      }
    },
    [enableGroupConfig, isEditing, submit]
  );

  return (
    <main className="bg-grey-1 w-full h-full p-2">
      {/*
       * The <form> is styled as a constraining container that determines
       * the Card's dimensions. The flex-column layout constrains content
       * (including scrolling content) to the available height.
       */}
      <form
        action={formAction}
        className={classnames(
          'w-[640px] max-w-[90vw] mx-auto',
          'flex flex-col min-h-0 h-full space-y-2'
        )}
        method="POST"
        onSubmit={onSubmit}
      >
        {isEditing && (
          <RouterLink href="/app/basic-lti-launch" data-testid="back-link">
            <Link classes="flex gap-x-1 items-center" underline="always">
              <ArrowLeftIcon className="w-[0.875em] h-[0.875em]" />
              Back to assignment
            </Link>
          </RouterLink>
        )}
        {/* Card constrains overflow-scroll children to height constraints */}
        <Card classes="flex flex-col min-h-0">
          <CardHeader variant="secondary" title="Assignment details" />
          <Scroll>
            <CardContent size="lg">
              {/* 1-col grid for very narrow screens; 2-col for everyone else */}
              <div className="grid grid-cols-1 sm:grid-cols-[10rem_1fr] gap-x-6 gap-y-3">
                <PanelLabel
                  description={<p>Select content for your assignment</p>}
                  isCurrentStep={currentStep === 'content-selection'}
                >
                  Assignment content
                </PanelLabel>

                <div data-testid="content-selector-container">
                  {content && currentStep !== 'content-selection' ? (
                    <div className="flex gap-x-2 items-center">
                      <span
                        className="break-words italic"
                        data-testid="content-summary"
                      >
                        {contentDescription(content)}
                      </span>
                      <LinkButton
                        onClick={() => setEditingContent(true)}
                        data-testid="edit-content"
                        title="Change assignment content"
                        underline="always"
                      >
                        Change
                      </LinkButton>
                    </div>
                  ) : (
                    <ContentSelector
                      initialContent={content ?? undefined}
                      onSelectContent={selectContent}
                      onError={setErrorInfo}
                    />
                  )}
                </div>
                {currentStep === 'group-configuration' && (
                  <>
                    <div className="sm:col-span-2 border-b" />
                    <PanelLabel isCurrentStep={true}>
                      Group assignment
                    </PanelLabel>
                    <div
                      className={classnames(
                        // Set a height on this container to give the group
                        // <select> element room when it renders (avoid
                        // changing the height of the Card later)
                        'h-28'
                      )}
                    >
                      <GroupConfigSelector
                        groupConfig={groupConfig}
                        onChangeGroupConfig={setGroupConfig}
                      />
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Scroll>
          {
            // See comments in `selectContent` about auto-submitting form if
            // this is a new assignment and groups are not available.
            (editingContent || currentStep === 'group-configuration') && (
              <CardContent size="lg">
                <CardActions>
                  {editingContent && (
                    <Button
                      onClick={() => setEditingContent(false)}
                      data-testid="cancel-edit-content"
                    >
                      Back
                    </Button>
                  )}
                  {!editingContent && content && (
                    <Button
                      data-testid="save-button"
                      disabled={
                        groupConfig.useGroupSet && !groupConfig.groupSet
                      }
                      variant="primary"
                      onClick={() => submit(content)}
                    >
                      {isEditing ? 'Save' : 'Continue'}
                    </Button>
                  )}
                </CardActions>
              </CardContent>
            )
          }
          {content && (
            <FilePickerFormFields
              content={content}
              formFields={{ ...formFields, ...deepLinkingFields }}
              groupSet={groupConfig.useGroupSet ? groupConfig.groupSet : null}
            />
          )}
          <input style={{ display: 'none' }} ref={submitButton} type="submit" />
        </Card>
        {shouldSubmit && <SpinnerOverlay />}
        {errorInfo && (
          <ErrorModal
            description={errorInfo.message}
            error={errorInfo.error}
            onCancel={() => setErrorInfo(null)}
          />
        )}
      </form>
    </main>
  );
}
