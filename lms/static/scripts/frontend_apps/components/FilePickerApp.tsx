import {
  ArrowLeftIcon,
  Button,
  Card,
  CardActions,
  Checkbox,
  CheckboxCheckedFilledIcon,
  InfoIcon,
  CardContent,
  CardHeader,
  Link,
  LinkButton,
  Input,
  Scroll,
  SpinnerOverlay,
  IconButton,
  Popover,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { ComponentChildren } from 'preact';
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from 'preact/hooks';
import { Link as RouterLink } from 'wouter-preact';

import type { AutoGradingConfig as APIAutoGradingConfig } from '../api-types';
import { useConfig } from '../config';
import type { ConfigObject } from '../config';
import { apiCall } from '../utils/api';
import type { Content, URLContent } from '../utils/content-item';
import { truncateURL } from '../utils/format';
import { useUniqueId } from '../utils/hooks';
import type { AssignmentType } from './AssignmentTypeSelector';
import AssignmentTypeSelector from './AssignmentTypeSelector';
import type {
  AutoGradingConfig,
  AutoGradingConfiguratorHandle,
  GradingPhase,
} from './AutoGradingConfigurator';
import AutoGradingConfigurator, {
  defaultAutoGradingConfig,
  fromAPIConfig,
  toAPIConfig,
} from './AutoGradingConfigurator';
import type { CheckpointType } from './CheckpointSelector';
import CheckpointSelector from './CheckpointSelector';
import ContentSelector from './ContentSelector';
import type { DueDateSelectorHandle } from './DueDateSelector';
import DueDateSelector from './DueDateSelector';
import ErrorModal from './ErrorModal';
import FilePickerFormFields from './FilePickerFormFields';
import GroupConfigSelector from './GroupConfigSelector';
import type { GroupConfig } from './GroupConfigSelector';
import HiddenFormFields from './HiddenFormFields';

export type ErrorInfo = {
  message: string;
  error: Error;
};

export type FilePickerAppProps = {
  /** Callback invoked when the form is submitted */
  onSubmit?: (e: Event) => void;
};

/* A step or 'screen' of the assignment configuration */
type PickerStep =
  // First screen (only shown when more than one assignment type is available)
  // where the instructor picks the type of assignment they are creating.
  | 'assignment-type'
  // "Hide & Reveal" screens, only shown when that assignment type is chosen.
  | 'checkpoint'
  | 'due-date'
  | 'content-selection'
  // Final screen where the settings for the assignment are shown, and also
  // additional settings which don't need a whole screen.
  | 'details';

/**
 * Sub-steps of the assignment-type workflow shown before the regular file
 * picker flow. These are the `PickerStep`s that precede content selection, plus
 * `done`, which means the workflow has been completed (or skipped) and the
 * regular flow takes over. Derived from `PickerStep` so the two stay in sync.
 */
type WorkflowStep =
  | Exclude<PickerStep, 'content-selection' | 'details'>
  | 'done';

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
  if (content.url.startsWith('canvas-studio://')) {
    return 'Video in Canvas Studio';
  }
  if (content.url.startsWith('canvas://file')) {
    return 'PDF file in Canvas';
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
    /* istanbul ignore next: defensive — content type is always 'url' here */
    default:
      throw new Error('Unknown content type');
  }
}

function contentFromURL(url: string): Content {
  return { type: 'url', url };
}

function localDateTime(date: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0');
  return (
    `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}` +
    `T${pad(date.getHours())}:${pad(date.getMinutes())}`
  );
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
  config: ConfigObject,
): Promise<ConfigObject> {
  if (!config.editing) {
    throw new Error('Assignment editing config missing');
  }

  const authToken = config.api!.authToken;
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
  verticalAlign = 'top',
}: {
  children: ComponentChildren;
  description?: ComponentChildren;
  isCurrentStep: boolean;
  verticalAlign?: 'top' | 'center';
}) {
  return (
    <div
      className={classnames('space-y-1.5 leading-none', {
        'flex flex-col justify-center': verticalAlign === 'center',
      })}
    >
      <div className="sm:text-end font-medium text-slate-600 uppercase">
        {children}
      </div>
      {isCurrentStep && description && (
        <div className="sm:text-end font-normal text-stone-500">
          {description}
        </div>
      )}
    </div>
  );
}

type DeepLinkingAPIData = Record<string, unknown> & {
  // One config for a single grade; one per grading phase for paced grades.
  auto_grading_config: APIAutoGradingConfig | APIAutoGradingConfig[] | null;
};

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
    editing,
    filePicker: {
      autoGradingEnabled,
      assignmentTypes,
      deepLinkingAPI,
      formAction,
      formFields,
      promptForTitle,
      promptForGradable,
    },
  } = useConfig(['api', 'filePicker']);

  // Assignment types the instructor can choose from. `reading` is always
  // available; other types (e.g. `hide_and_reveal`) are gated by the backend
  // via a per-install feature flag. Until the backend sends `assignmentTypes`,
  // we fall back to `reading` only, which keeps the type workflow dormant.
  const availableAssignmentTypes = assignmentTypes ?? ['reading'];

  // The multi-step type workflow (type selection + any type-specific sub-steps)
  // is only worth showing when there is more than one type to pick from. With a
  // single type there is nothing to choose, so we skip straight to the regular
  // flow. This intentionally does *not* depend on any single type being enabled,
  // so adding a new type keeps the workflow working without changes here.
  const enableTypeWorkflow = availableAssignmentTypes.length > 1;

  // Currently selected content for assignment.
  const [content, setContent] = useState<Content | null>(
    assignment ? contentFromURL(assignment.document.url) : null,
  );

  const [autoGradingConfig, setAutoGradingConfig] = useState<AutoGradingConfig>(
    () => {
      const assignmentAutoGradingConfig = assignment?.auto_grading_config;
      if (!assignmentAutoGradingConfig) {
        return defaultAutoGradingConfig();
      }

      // Initialize with the assignment's auto-grading config if it exists
      return fromAPIConfig(assignmentAutoGradingConfig);
    },
  );

  // Flag indicating if we are editing content that was previously selected.
  const [editingContent, setEditingContent] = useState(false);
  // True if we are editing an existing assignment configuration.
  const isEditing = !!assignment;

  // "Back to assignment" only makes sense for the in-app edit (reconfigure),
  // which carries `editing` config and has an assignment launch to return to.
  // The deep-linking file picker (e.g. Canvas "edit") is a standalone page with
  // nowhere to go back to, so the link would dead-end there.
  const canReturnToAssignment = isEditing && !!editing;

  // Type of assignment being created, chosen in the first ("assignment-type")
  // step of the workflow. Only relevant when `enableTypeWorkflow`.
  //
  // When editing there is no workflow to choose it in, so it comes from the
  // assignment and from nowhere else -- the default below is for assignments
  // that do not exist yet, and falling through to it would answer "what type
  // is this assignment?" with "whichever this install offers first".
  //
  // Getting this wrong on an edit is not cosmetic in either direction. The
  // type says how many grading phases there are, and saving fewer than the
  // assignment has deletes the rest; it also drives `checkpoint_enabled`,
  // which the backend can only ever turn on, so an edit that reads the type
  // wrong converts the assignment for good.
  const [assignmentType, setAssignmentType] = useState<AssignmentType>(() => {
    if (assignment) {
      return assignment.checkpoint_enabled ? 'hide_and_reveal' : 'reading';
    }

    // The first type the backend offers, so it is always one it accepts.
    return availableAssignmentTypes[0] ?? 'reading';
  });
  // Checkpoint configuration for "Hide & Reveal" assignments.
  const [checkpointType, setCheckpointType] =
    useState<CheckpointType>('manual');
  // The date the assignment already carries, if any, in the selector's local
  // `YYYY-MM-DDTHH:MM` form. What the picker is given is what it sends back, so
  // starting empty would clear a date the assignment already has. The backend
  // sends UTC; the selector works in local time.
  const savedDueDate = assignment?.due_date
    ? localDateTime(new Date(assignment.due_date))
    : null;
  // The same date in the UTC ISO form the backend speaks, for handing back
  // unchanged when the instructor was never shown a control over it.
  const savedDueDateISO = assignment?.due_date
    ? new Date(assignment.due_date).toISOString()
    : null;
  const [dueDate, setDueDate] = useState<string | null>(savedDueDate);
  // The due date is optional, and "none yet" and "not wanted" look the same in
  // `dueDate`, so whether the fields are on is its own state.
  const [dueDateEnabled, setDueDateEnabled] = useState(!!assignment?.due_date);
  // The due date is optional, but when set it must be complete and in the
  // future. The fields — and the checks over them — live in `DueDateSelector`;
  // this handle triggers them before leaving the due-date step, and the
  // selector presents any error itself. The value is a local
  // `YYYY-MM-DDTHH:MM` string, converted to UTC on submit.
  const dueDateSelectorRef = useRef<DueDateSelectorHandle | null>(null);
  // Only the selected phase's goal inputs are mounted, so the form's own
  // `reportValidity` cannot see the others. This handle checks them all.
  const autoGradingRef = useRef<AutoGradingConfiguratorHandle | null>(null);
  // Recomputed on each render rather than memoized on mount, so "now" cannot go
  // stale while the picker sits open.
  const now = localDateTime(new Date());
  // An assignment being edited can have a due date that has already passed, and
  // holding it to "must be in the future" would block every unrelated edit:
  // `validate` runs on submit, so a date it rejects is a date that stops the
  // whole save. The date already saved is therefore allowed to stand; anything
  // earlier than it still isn't. `YYYY-MM-DDTHH:MM` strings compare
  // lexicographically, so this is a plain string comparison.
  const minDueDate = savedDueDate && savedDueDate < now ? savedDueDate : now;

  // A checkpoint ("Hide & Reveal") assignment is being created when the
  // instructor picked that type in the workflow. This drives the
  // `checkpoint_enabled` field the backend persists.
  const checkpointEnabled = assignmentType === 'hide_and_reveal';

  // Whether the due-date control is on screen at all. `pacedControls` goes
  // inside the auto-grading block, which is mounted only when the install
  // offers auto grading and the instructor turned it on, and inside the
  // configurator's own "there is more than one phase to pace" check. The mode
  // is deliberately not part of this: with a single grade the control is still
  // rendered, disabled, saying why the date does not apply.
  const dueDateControlShown =
    autoGradingEnabled && autoGradingConfig.enabled && checkpointEnabled;

  // Whether the assignment is graded phase by phase. The due date only applies
  // then -- a single grade counts the whole assignment, so there is nothing
  // for a date to cut off.
  const pacedGrades = dueDateControlShown && autoGradingConfig.mode === 'paced';

  // UTC ISO string for the backend. Both submit paths send this same value.
  //
  // The backend takes what the picker sends as the whole truth: no field means
  // no date. So the date follows the control, and the two cases where it is
  // not editable are not the same case:
  //
  // With a single grade, nothing is sent. The date has no meaning there, and
  // the instructor is looking at the control while it says so -- clearing it
  // is an answer to something they can see. Gated rather than cleared, so
  // switching back to Paced grades brings the date back; the phase goals
  // behave the same way.
  //
  // With no control on screen at all -- auto grading off, or an install that
  // does not offer it -- the date the assignment came in with is handed back
  // untouched. There is no mode to honour here, only state nobody chose, and
  // the date is not an auto-grading property: `enable_toolbar_checkpoint` and
  // `enable_student_checkpoint` publish it for every checkpoint assignment. An
  // edit about a document URL should not take it off the students' toolbars.
  const dueDateISO = dueDateControlShown
    ? pacedGrades && dueDate
      ? new Date(dueDate).toISOString()
      : null
    : savedDueDateISO;

  const toggleDueDate = (enabled: boolean) => {
    setDueDateEnabled(enabled);
    // Turning it off drops the date: a hidden field still being sent is how a
    // due date nobody can see ends up on the assignment.
    if (!enabled) {
      setDueDate(null);
    }
  };

  // Spelled out here rather than read from anywhere: the assignment doesn't
  // exist yet, so nothing else knows how many phases it will be graded in. One
  // checkpoint means two phases; more checkpoints would only make this list
  // longer.
  const gradingPhases: GradingPhase[] = checkpointEnabled
    ? [
        {
          label: 'Checkpoint',
          description: 'Applies to activity before the Checkpoint',
        },
        {
          label: dueDate ? 'Due Date' : 'Assignment end',
          description: 'Applies to activity after the Checkpoint',
        },
      ]
    : [];

  // The auto-grading config as expected by the backend
  const autoGradingConfigToSave:
    | APIAutoGradingConfig
    | APIAutoGradingConfig[]
    | null = useMemo(
    () =>
      autoGradingEnabled && autoGradingConfig.enabled
        ? toAPIConfig(autoGradingConfig, gradingPhases.length)
        : null,
    [autoGradingConfig, autoGradingEnabled, gradingPhases.length],
  );
  // Current sub-step of the assignment-type workflow. When the workflow isn't
  // enabled we start as `done` so it is skipped entirely.
  const [workflowStep, setWorkflowStep] = useState<WorkflowStep>(
    enableTypeWorkflow ? 'assignment-type' : 'done',
  );

  // Advance to the next sub-step of the workflow. Only "hide_and_reveal" has
  // further steps (checkpoint, due-date); other types go straight to the
  // regular flow.
  const goToNextWorkflowStep = () => {
    // A half-entered due date leaves `dueDate` null here, indistinguishable
    // from the legal "left blank", and a complete one can have fallen into
    // the past. Only the selector can tell; it shows the reason for any
    // rejection itself.
    /* istanbul ignore next: unreachable while the due-date step is skipped */
    if (
      workflowStep === 'due-date' &&
      dueDateSelectorRef.current &&
      !dueDateSelectorRef.current.validate()
    ) {
      return;
    }
    // TEMPORARY: the due-date step is skipped because the
    // date it collects has no effect yet, and offering it suggests the
    // assignment does something it doesn't. Nothing else about the step was
    // removed — to turn it back on, restore the commented-out line below in
    // place of the one under it, and the blocks commented out in
    // `FilePickerApp-test`.
    //
    // From 'checkpoint' the next step is 'due-date'; from 'due-date' (the last
    // step) the workflow is done. The 'assignment-type' step has no "Next" — it
    // advances directly on selection (see `selectAssignmentType`).
    // setWorkflowStep(step => (step === 'checkpoint' ? 'due-date' : 'done'));
    setWorkflowStep('done');
  };

  // Pick an assignment type in the first workflow step. Unlike the later steps,
  // this advances immediately (the step has no "Next" button, mirroring the
  // content-selection buttons): "hide_and_reveal" continues to the checkpoint
  // sub-steps; other types go straight to the regular flow.
  const selectAssignmentType = (type: AssignmentType) => {
    setAssignmentType(type);
    setWorkflowStep(type === 'hide_and_reveal' ? 'checkpoint' : 'done');
  };

  // Go back to the previous sub-step of the workflow. Only ever invoked from
  // the 'checkpoint' and 'due-date' steps (the "Back" button is
  // hidden on the first step). Selections made in later steps are kept in state,
  // so they survive going back and forth.
  const goToPreviousWorkflowStep = () => {
    setWorkflowStep(step =>
      step === 'due-date' ? 'checkpoint' : 'assignment-type',
    );
  };

  // Jump straight back to the assignment-mode selection from anywhere in the
  // Paced ("Hide & Reveal") sub-steps, via the close button in the card header.
  // Selections made so far are kept in state.
  const returnToModeSelection = () => setWorkflowStep('assignment-type');

  // Whether there are additional configuration options to present after the
  // user has selected the content for the assignment.
  const showDetailsScreen =
    enableGroupConfig ||
    promptForTitle ||
    promptForGradable ||
    autoGradingEnabled;

  let currentStep: PickerStep;
  if (enableTypeWorkflow && workflowStep !== 'done' && !isEditing) {
    // While the assignment-type workflow is in progress, its current sub-step
    // (which is a subset of PickerStep) is the active step.
    currentStep = workflowStep;
  } else if (editingContent) {
    currentStep = 'content-selection';
  } else if (isEditing) {
    currentStep = 'details';
  } else {
    currentStep =
      content && showDetailsScreen ? 'details' : 'content-selection';
  }

  // Whether the current step belongs to the assignment-type workflow shown
  // before the regular file picker flow.
  const inTypeWorkflow =
    currentStep === 'assignment-type' ||
    currentStep === 'checkpoint' ||
    currentStep === 'due-date';

  // The first workflow step has nothing before it, so "Back" is only offered on
  // later steps.
  const canGoBackInWorkflow =
    currentStep === 'checkpoint' || currentStep === 'due-date';

  // Title shown in the card header, which changes depending on the current step.
  const stepTitles: Record<PickerStep, string> = {
    'assignment-type': 'Assignment mode',
    checkpoint: 'Paced Social Annotation',
    'due-date': 'Paced Social Annotation',
    'content-selection': 'Assignment details',
    details: 'Assignment details',
  };
  const cardTitle = stepTitles[currentStep];

  const [groupConfig, setGroupConfig] = useState<GroupConfig>({
    useGroupSet: !!assignment?.group_set_id,
    groupSet: assignment?.group_set_id ?? null,
  });

  const [title, setTitle] = useState(
    promptForTitle ? 'Hypothesis assignment' : null,
  );

  const [assignmentGradableMaxPoints, setAssignmentGradableMaxPoints] =
    useState('');
  const gradableMaxInputId = useUniqueId('gradable-max-input');

  const titleInputId = useUniqueId('title-input');

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

  const formRef = useRef<HTMLFormElement>(null);
  const iconRef = useRef<HTMLButtonElement | null>(null);
  const [maxPointsPopoverOpen, setMaxPointsPopoverOpen] = useState(false);

  const submit = useCallback(
    async (content: Content) => {
      // Validate form fields which are shown on the details screen.
      if (!formRef.current?.reportValidity()) {
        return;
      }

      // Only the selected grading phase has its goal inputs mounted, so
      // `reportValidity` above checked one phase out of however many there
      // are. This switches to the first phase left without a goal and reports
      // it there. Left unchecked, a phase would save a goal of zero, which the
      // proportional grade then divides by.
      if (autoGradingRef.current && !autoGradingRef.current.validate()) {
        return;
      }

      // A half-entered due date leaves `dueDate` null, indistinguishable from
      // the legal "left blank", and a complete one can have fallen into the
      // past. Only the selector can tell; it shows the reason itself. The time
      // field is a custom listbox, so `reportValidity` above does not see it.
      if (
        dueDateSelectorRef.current &&
        !dueDateSelectorRef.current.validate()
      ) {
        return;
      }

      // Set shouldSubmit to true early to show the spinner while fetching form fields
      setShouldSubmit(true);

      if (!deepLinkingAPI || deepLinkingFields) {
        return;
      }

      // When deepLinkingAPI is present we want to call the backend to return the form
      // fields we'll forward to the LMS to complete the Deep Linking request
      try {
        const data: DeepLinkingAPIData = {
          ...deepLinkingAPI.data,
          auto_grading_config: autoGradingConfigToSave,
          checkpoint_enabled: checkpointEnabled,
          due_date: dueDateISO,
          content,
          group_set: groupConfig.useGroupSet ? groupConfig.groupSet : null,
          title,
          assignment_gradable_max_points:
            assignmentGradableMaxPoints === ''
              ? null
              : Number(assignmentGradableMaxPoints),
        };
        setDeepLinkingFields(
          await apiCall({
            authToken: authToken,
            path: deepLinkingAPI.path,
            data,
          }),
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
      checkpointEnabled,
      dueDateISO,
      deepLinkingFields,
      deepLinkingAPI,
      groupConfig.groupSet,
      groupConfig.useGroupSet,
      title,
      autoGradingConfigToSave,
      assignmentGradableMaxPoints,
    ],
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
      //
      // TODO - This could be simplified by using `HTMLFormElement.requestSubmit`
      // *if available* instead of `HTMLFormElement.submit`, as `requestSubmit`
      // _does_ trigger the "submit" event.
      submitButton.current!.click();
    }
  }, [shouldSubmit, deepLinkingAPI, deepLinkingFields]);

  const selectContent = useCallback(
    (content: Content) => {
      setContent(content);
      setEditingContent(false);

      // If this is a new assignment and the only choice the user has to make
      // is the content, we submit as soon as they select the content.
      if (!isEditing && !showDetailsScreen) {
        submit(content);
      }
    },
    [isEditing, showDetailsScreen, submit],
  );

  // Whether the Save / Continue button should be enabled. This doesn't take
  // into account the state of some input fields whose validity is checked via
  // `HTMLFormElement.checkValidity` on submission.
  const canSubmit =
    content !== null &&
    (!groupConfig.useGroupSet || groupConfig.groupSet !== null);

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
          'flex flex-col min-h-0 h-full space-y-2',
        )}
        method="POST"
        onSubmit={e => {
          // If `shouldSubmit` is false, this submit was triggered by an
          // implicit form submission. Route it through the same code as an
          // explicit click on Save / Continue.
          if (!shouldSubmit) {
            e.preventDefault();
            if (canSubmit) {
              submit(content);
            }
            return;
          }
          onSubmit?.(e);
        }}
        ref={formRef}
      >
        {canReturnToAssignment && (
          <RouterLink
            href="/app/basic-lti-launch"
            data-testid="back-link"
            asChild
          >
            <Link classes="flex gap-x-1 items-center" underline="always">
              <ArrowLeftIcon className="w-[0.875em] h-[0.875em]" />
              Back to assignment
            </Link>
          </RouterLink>
        )}
        {/* Card constrains overflow-scroll children to height constraints */}
        <Card classes="flex flex-col min-h-0 overflow-hidden">
          <CardHeader
            variant="secondary"
            title={cardTitle}
            // Offer a close ("x") button to return to mode selection from the
            // Paced sub-steps (checkpoint / due-date), but not from the mode
            // selection step itself or the regular flow.
            onClose={canGoBackInWorkflow ? returnToModeSelection : undefined}
          />
          <Scroll>
            <CardContent size="lg">
              {inTypeWorkflow ? (
                <div className="space-y-4">
                  {currentStep === 'assignment-type' && (
                    <AssignmentTypeSelector
                      types={availableAssignmentTypes}
                      onSelect={selectAssignmentType}
                    />
                  )}
                  {currentStep === 'checkpoint' && (
                    <CheckpointSelector
                      selected={checkpointType}
                      onChange={setCheckpointType}
                    />
                  )}
                  {currentStep === 'due-date' && (
                    <DueDateSelector
                      dueDate={dueDate}
                      onChange={setDueDate}
                      min={minDueDate}
                      selectorRef={dueDateSelectorRef}
                    />
                  )}
                </div>
              ) : (
                /* 1-col grid for very narrow screens; 2-col for everyone else */
                <div className="grid grid-cols-1 sm:grid-cols-[10rem_1fr] gap-x-6 gap-y-3">
                  <PanelLabel
                    description={<p>Select content for your assignment</p>}
                    isCurrentStep={currentStep === 'content-selection'}
                  >
                    Assignment content
                  </PanelLabel>

                  <div data-testid="content-selector-container">
                    {content && currentStep !== 'content-selection' ? (
                      <div className="flex gap-x-2 items-start">
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
                  {currentStep === 'details' && (
                    <>
                      {typeof title === 'string' && (
                        <>
                          <div className="sm:col-span-2 border-b" />
                          <PanelLabel isCurrentStep verticalAlign="center">
                            Title
                          </PanelLabel>
                          <Input
                            data-testid="title-input"
                            id={titleInputId}
                            // Max length is based on what D2L supports, which is the first LMS that
                            // supported setting a title in assignment configuration.
                            maxLength={150}
                            onInput={(e: Event) =>
                              setTitle((e.target as HTMLInputElement).value)
                            }
                            required
                            value={title}
                          />
                        </>
                      )}
                      {promptForGradable && (
                        <>
                          <div className="sm:col-span-2 border-b" />
                          <PanelLabel isCurrentStep verticalAlign="center">
                            <div className="flex items-center sm:justify-end">
                              Max points
                              <IconButton
                                icon={InfoIcon}
                                title="About max points"
                                onClick={() =>
                                  setMaxPointsPopoverOpen(open => !open)
                                }
                                expanded={maxPointsPopoverOpen}
                                elementRef={iconRef}
                                // Align right side of the icon with the right
                                // edge of the text labels above and below.
                                // Do it by setting negative margin that
                                // compensates for the button's padding.
                                classes="text-[16px] -mr-2 touch:-mr-[12px]"
                              />
                            </div>
                          </PanelLabel>
                          <Input
                            data-testid="gradable-max-input"
                            id={gradableMaxInputId}
                            type="number"
                            placeholder={'ex: 100'}
                            min={0}
                            value={assignmentGradableMaxPoints}
                            onChange={e =>
                              setAssignmentGradableMaxPoints(
                                (e.target as HTMLInputElement).value,
                              )
                            }
                          />
                          <Popover
                            open={maxPointsPopoverOpen}
                            anchorElementRef={iconRef}
                            onClose={() => setMaxPointsPopoverOpen(false)}
                            classes="p-2"
                            placement="above"
                            arrow
                          >
                            <div className="flex flex-col gap-y-2">
                              Optionally add a max points value here instead of
                              using your LMS grading settings.
                              <Link
                                href="https://web.hypothes.is/help/max-points-in-hypothesis-enabled-readings/"
                                underline="always"
                                target="_blank"
                              >
                                Learn more about our max points feature
                              </Link>
                            </div>
                          </Popover>
                        </>
                      )}

                      {autoGradingEnabled && (
                        <>
                          <div className="sm:col-span-2 border-b" />
                          <PanelLabel isCurrentStep>Auto grading</PanelLabel>
                          <AutoGradingConfigurator
                            config={autoGradingConfig}
                            onChange={setAutoGradingConfig}
                            configuratorRef={autoGradingRef}
                            gradingPhases={gradingPhases}
                            pacedControls={
                              <div className="space-y-2">
                                <Checkbox
                                  checked={dueDateEnabled && pacedGrades}
                                  disabled={!pacedGrades}
                                  checkedIcon={CheckboxCheckedFilledIcon}
                                  data-testid="due-date-toggle"
                                  onChange={e =>
                                    toggleDueDate(
                                      (e.target as HTMLInputElement).checked,
                                    )
                                  }
                                >
                                  Optional: Assignment Due Date
                                </Checkbox>
                                {!pacedGrades && (
                                  <p
                                    className="text-stone-500 ml-7"
                                    data-testid="due-date-unavailable"
                                  >
                                    Available with Paced grades, which stops
                                    counting at the date.
                                  </p>
                                )}
                                {pacedGrades && dueDateEnabled && (
                                  <DueDateSelector
                                    dueDate={dueDate}
                                    onChange={setDueDate}
                                    min={minDueDate}
                                    selectorRef={dueDateSelectorRef}
                                  />
                                )}
                              </div>
                            }
                          />
                        </>
                      )}
                      {enableGroupConfig && (
                        <>
                          <div className="sm:col-span-2 border-b" />
                          <PanelLabel isCurrentStep>
                            Group assignment
                          </PanelLabel>
                          <div
                            className={classnames(
                              // Set a height on this container to give the group
                              // <select> element room when it renders (avoid
                              // changing the height of the Card later)
                              'h-28',
                            )}
                          >
                            <GroupConfigSelector
                              groupConfig={groupConfig}
                              onChangeGroupConfig={setGroupConfig}
                            />
                          </div>
                        </>
                      )}
                    </>
                  )}
                </div>
              )}
            </CardContent>
          </Scroll>
          {/* The assignment-type step advances on selection, so navigation
              buttons only appear on the later workflow steps. */}
          {canGoBackInWorkflow && (
            <CardContent size="lg">
              <CardActions>
                <Button
                  data-testid="workflow-back-button"
                  onClick={goToPreviousWorkflowStep}
                >
                  Back
                </Button>
                <Button
                  data-testid="workflow-next-button"
                  variant="primary"
                  onClick={goToNextWorkflowStep}
                >
                  Next
                </Button>
              </CardActions>
            </CardContent>
          )}
          {
            // See comments in `selectContent` about auto-submitting form.
            (editingContent || currentStep === 'details') && (
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
                      disabled={!canSubmit}
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
          {
            // Render different fields depending on whether we are
            // submitting the form to our backend, or to the LMS (aka. deep linking)
            content && !deepLinkingFields && (
              <FilePickerFormFields
                title={title}
                content={content}
                formFields={formFields}
                groupSet={groupConfig.useGroupSet ? groupConfig.groupSet : null}
                autoGradingConfig={autoGradingConfigToSave}
                checkpointEnabled={checkpointEnabled}
                dueDate={dueDateISO}
              />
            )
          }
          {
            // Or deep linking, submitting the form to the LMS.
            content && deepLinkingFields && (
              <HiddenFormFields fields={deepLinkingFields} />
            )
          }

          <input
            disabled={!canSubmit}
            style={{ display: 'none' }}
            ref={submitButton}
            type="submit"
          />
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
