import {
  Checkbox,
  CheckboxCheckedFilledIcon,
  Input,
  RadioGroup,
  Tab,
  TabList,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { ComponentChildren, Ref } from 'preact';
import {
  useCallback,
  useId,
  useImperativeHandle,
  useState,
} from 'preact/hooks';

import type {
  ActivityCalculation,
  GradingType,
  AutoGradingConfig as APIAutoGradingConfig,
} from '../api-types';
import UIMessage from './UIMessage';

/**
 * Required activity of one grading phase, or of the whole assignment when it
 * gets a single grade.
 */
export type PhaseGoals = {
  /**
   * Required number of annotations if the activity calculation is 'separate',
   * or the combined number of annotations and replies otherwise.
   */
  required_annotations: number;

  /** Required number of replies if the activity calculation is 'separate'. */
  required_replies?: number;
};

/** What the whole-assignment goals start at, as they always have. */
export const DEFAULT_SINGLE_GOALS: PhaseGoals = { required_annotations: 1 };

/**
 * What a grading phase's goals start at: nothing set yet.
 *
 * Zero rather than one, so that a phase the instructor never opened reads as
 * unset -- it shows the "Not set" badge, and `validate` refuses to submit it.
 * The number inputs have `min=1`, so zero is never a value they can settle on;
 * it only ever means "untouched", or "cleared just now".
 */
export const UNSET_PHASE_GOALS: PhaseGoals = { required_annotations: 0 };

/** The config an assignment starts with, before anything is set. */
export function defaultAutoGradingConfig(): AutoGradingConfig {
  return {
    enabled: false,
    mode: 'single',
    grading_type: 'scaled',
    activity_calculation: 'cumulative',
    single: DEFAULT_SINGLE_GOALS,
    phases: [],
  };
}

export type AutoGradingConfig = {
  /** Whether auto grading is enabled for the assignment or not */
  enabled?: boolean;

  /**
   * Whether the assignment gets one grade for the whole of it, or one per
   * grading phase.
   *
   * Not persisted as such: the backend stores one config per phase, so the
   * mode is read back off how many of them come out (see `fromAPIConfig`).
   */
  mode: 'single' | 'paced';

  grading_type: GradingType;
  activity_calculation: ActivityCalculation;

  /**
   * Goals used in 'single' mode.
   *
   * Held apart from `phases` so that switching modes back and forth doesn't
   * overwrite either set of numbers.
   */
  single: PhaseGoals;

  /** Goals of each grading phase, in phase order. Used in 'paced' mode. */
  phases: PhaseGoals[];
};

/** One of the grading phases an assignment can be configured with. */
export type GradingPhase = {
  /** Tab label, e.g. 'Checkpoint' or 'Due Date'. */
  label: string;

  /** Which activity the phase covers, shown above its goals. */
  description: string;
};

/**
 * The goals of each grading phase, with the phases the instructor never
 * touched left unset.
 *
 * `phases` only holds what was edited, so both what is shown and what is saved
 * read it through here. Saving it raw would send an empty list for a config
 * left untouched, and an empty list means "no auto grading".
 */
export function phaseGoalsOf(
  config: AutoGradingConfig,
  phaseCount: number,
): PhaseGoals[] {
  return Array.from({ length: phaseCount }, (_, index) =>
    index < config.phases.length ? config.phases[index] : UNSET_PHASE_GOALS,
  );
}

/**
 * Turn the local config into what the backend persists: one config for a
 * single grade, one per phase for paced grades.
 *
 * The shape is preserved rather than always sent as a list. An assignment with
 * one grading phase keeps sending exactly what it sent before paced grades
 * existed, which is also what assignments created back then still carry in
 * their LTI custom params.
 */
export function toAPIConfig(
  config: AutoGradingConfig,
  phaseCount: number,
): APIAutoGradingConfig | APIAutoGradingConfig[] {
  const { mode, grading_type, activity_calculation, single } = config;
  const withGradingOptions = (goals: PhaseGoals): APIAutoGradingConfig => ({
    grading_type,
    activity_calculation,
    ...goals,
  });

  // Fewer than two phases means there is nothing to pace, whatever the mode
  // says. It also keeps the list from ever going out empty, which the backend
  // reads as "no auto grading" and acts on by deleting the config.
  return mode === 'single' || phaseCount < 2
    ? withGradingOptions(single)
    : phaseGoalsOf(config, phaseCount).map(withGradingOptions);
}

/**
 * Rebuild the local config out of what the backend stored, for the edit flow.
 *
 * The grading type and the activity calculation are shared by every phase, so
 * the first one speaks for all of them.
 */
export function fromAPIConfig(
  config: APIAutoGradingConfig | APIAutoGradingConfig[],
): AutoGradingConfig {
  const apiPhases = Array.isArray(config) ? config : [config];
  if (apiPhases.length === 0) {
    // No config at all, which the backend sends as nothing rather than as an
    // empty list. Guarded because this is exported, and the alternative is
    // reading the grading options off `undefined`.
    return defaultAutoGradingConfig();
  }

  const [first] = apiPhases;
  // Only the goals are per phase; the two grading options above are shared, so
  // they're dropped here and put back by `toAPIConfig`. A phase with no reply
  // goal keeps the key absent rather than holding a value, so a config
  // survives a round trip unchanged.
  //
  // `null` counts as absent too, spelled out because zero is a goal a phase
  // can legitimately have. The type says the key is optional, but
  // `AutoGradingConfig.asdict()` always sends it -- as `null` for a cumulative
  // config. Kept, that `null` reaches a number input as its value, where the
  // `= 0` default does not fire because destructuring defaults only answer to
  // `undefined`; the field renders empty and `required` then refuses the save
  // with nothing on screen saying why.
  const goals = apiPhases.map(
    ({ required_annotations, required_replies }): PhaseGoals => ({
      required_annotations,
      ...(required_replies === undefined || required_replies === null
        ? {}
        : { required_replies }),
    }),
  );

  return {
    enabled: true,
    mode: apiPhases.length > 1 ? 'paced' : 'single',
    grading_type: first.grading_type,
    activity_calculation: first.activity_calculation,
    // The first phase is the closest thing to a whole-assignment goal there
    // is, so it seeds the other mode instead of leaving it at the default.
    single: goals[0],
    phases: goals,
  };
}

/**
 * Whether a phase still has no goal.
 *
 * The annotations goal is the one the instructor has to fill in: its input is
 * `required` with a minimum of one, in both activity calculations, while the
 * replies goal accepts zero. So this is the same condition the browser would
 * report for a mounted field -- which is the point, since a phase in an
 * unselected tab has no mounted fields to report anything.
 *
 * It is also exactly what keeps grading safe: a proportional grade divides by
 * the annotations goal when activity is cumulative, and by the two goals
 * together when it is separate (`services/auto_grading.py`).
 */
function goalsAreUnset(goals: PhaseGoals): boolean {
  return !goals.required_annotations;
}

type AnnotationsGoalInputProps = {
  children?: ComponentChildren;
  gradingType: GradingType;
  value: number;
  onChange: (newValue: number) => void;

  /** Minimum required value for the input. Defaults to 1 */
  min?: number;
};

/**
 * Controls containing a number input to set the amount of required annotations
 * or replies
 */
function AnnotationsGoalInput({
  children,
  gradingType,
  value,
  onChange,
  min = 1,
}: AnnotationsGoalInputProps) {
  const inputId = useId();

  return (
    <div className="flex gap-2 items-center">
      <label
        className="grow flex justify-between items-center"
        htmlFor={inputId}
      >
        {children}
        <span className="uppercase font-semibold">
          {gradingType === 'all_or_nothing' ? 'Minimum' : 'Goal'}
        </span>
      </label>
      <Input
        id={inputId}
        classes="max-w-14"
        type="number"
        required
        min={min}
        step={1}
        value={value}
        onChange={e => onChange(Number((e.target as HTMLInputElement).value))}
      />
    </div>
  );
}

type PhaseGoalsFieldsProps = {
  goals: PhaseGoals;
  gradingType: GradingType;
  activityCalculation: ActivityCalculation;
  onChange: (newGoals: PhaseGoals) => void;
};

/**
 * The goals of one scope: a single row when annotations and replies are
 * tallied together, one row each when they are tallied separately.
 *
 * The same fields serve the single grade and every phase of a paced one.
 */
function PhaseGoalsFields({
  goals,
  gradingType,
  activityCalculation,
  onChange,
}: PhaseGoalsFieldsProps) {
  const {
    required_annotations: requiredAnnotations,
    required_replies: requiredReplies = 0,
  } = goals;

  return (
    <div className="flex flex-col gap-y-3">
      <AnnotationsGoalInput
        gradingType={gradingType}
        value={requiredAnnotations}
        onChange={requiredAnnotations =>
          onChange({ ...goals, required_annotations: requiredAnnotations })
        }
      >
        {activityCalculation === 'cumulative'
          ? 'Annotations and replies'
          : 'Annotations'}
      </AnnotationsGoalInput>
      {activityCalculation === 'separate' && (
        <AnnotationsGoalInput
          gradingType={gradingType}
          value={requiredReplies}
          onChange={requiredReplies =>
            onChange({ ...goals, required_replies: requiredReplies })
          }
          min={0}
        >
          Replies
        </AnnotationsGoalInput>
      )}
    </div>
  );
}

export type AutoGradingConfiguratorHandle = {
  /**
   * Check that every grading phase has a goal, switching to the first one that
   * doesn't and showing an error there, and return whether they all do.
   */
  validate(): boolean;
};

export type AutoGradingConfiguratorProps = {
  config: AutoGradingConfig;
  onChange: (newConfig: AutoGradingConfig) => void;

  /**
   * Ref through which the parent checks the goals before submitting.
   *
   * Needed because only the selected phase's inputs are mounted: the browser
   * cannot report a constraint on a field that isn't in the document, so
   * `reportValidity` on the form misses every phase but one.
   */
  configuratorRef?: Ref<AutoGradingConfiguratorHandle>;

  /**
   * Rendered under the grading-mode radios, in both grading modes.
   *
   * A slot rather than props of its own: what goes there is the assignment's
   * due date, and this component knows nothing about checkpoints. Whether it
   * is usable in the current mode is the caller's business.
   */
  pacedControls?: ComponentChildren;

  /**
   * The grading phases this assignment can be configured with, in phase order.
   *
   * Two or more of them turn paced grading on: the grading-mode radios, and a
   * tab per phase over the goals. With fewer -- the default -- the assignment
   * can only get a single grade, and this looks exactly as it did before paced
   * grades existed.
   */
  gradingPhases?: GradingPhase[];
};

/**
 * Allows instructors to enable auto grading for an assignment, and provide the
 * configuration to determine how to calculate each student's grade.
 */
export default function AutoGradingConfigurator({
  config,
  onChange,
  configuratorRef,
  pacedControls,
  gradingPhases = [],
}: AutoGradingConfiguratorProps) {
  const {
    enabled = false,
    mode,
    grading_type: gradingType,
    activity_calculation: activityCalculation,
  } = config;
  const updateConfig = useCallback(
    (newConfig: Partial<AutoGradingConfig>) =>
      onChange({ ...config, ...newConfig }),
    [config, onChange],
  );

  const gradingModeId = useId();
  const gradingTypeId = useId();
  const activityCalculationId = useId();
  const phasesId = useId();

  // There is nothing to pace unless the activity can be split in two.
  const paced = gradingPhases.length > 1;
  const [activePhase, setActivePhase] = useState(0);

  const phaseGoals = phaseGoalsOf(config, gradingPhases.length);
  const updatePhaseGoals = (index: number, newGoals: PhaseGoals) =>
    updateConfig({
      phases: phaseGoals.map((goals, i) => (i === index ? newGoals : goals)),
    });

  const showPhases = paced && mode === 'paced';

  // Whether a submit was already refused for a phase with no goal. Until then
  // an empty phase is not an error, just one the instructor hasn't reached.
  const [goalRefused, setGoalRefused] = useState(false);
  const activeGoalsUnset = showPhases && goalsAreUnset(phaseGoals[activePhase]);

  useImperativeHandle(
    configuratorRef ?? null,
    () => ({
      validate: () => {
        // With a single grade the only goals on screen are native inputs the
        // browser checks itself, and with auto grading off there are none.
        if (!enabled || !showPhases) {
          return true;
        }

        const unset = phaseGoals.findIndex(goalsAreUnset);
        if (unset === -1) {
          setGoalRefused(false);
          return true;
        }

        // Move to the offending phase so the message lands next to the field
        // it is about -- it may well be in a tab that isn't even mounted.
        setActivePhase(unset);
        setGoalRefused(true);
        return false;
      },
    }),
    [enabled, showPhases, phaseGoals],
  );

  return (
    <div className="flex flex-col gap-y-3">
      <Checkbox
        checked={enabled}
        checkedIcon={CheckboxCheckedFilledIcon}
        data-testid="auto-grading-toggle"
        onChange={e =>
          updateConfig({
            enabled: (e.target as HTMLInputElement).checked,
          })
        }
      >
        Enable automatic participation grading
      </Checkbox>
      {enabled && (
        <>
          {paced && (
            <>
              <div>
                <h3 id={gradingModeId} className="font-semibold mb-1">
                  Grading mode
                </h3>
                <RadioGroup
                  data-testid="grading-mode-radio-group"
                  aria-labelledby={gradingModeId}
                  selected={mode}
                  onChange={mode => updateConfig({ mode })}
                >
                  <RadioGroup.Radio
                    value="single"
                    subtitle={
                      <small>Counts activity across the whole assignment</small>
                    }
                  >
                    Single grade
                  </RadioGroup.Radio>
                  <RadioGroup.Radio
                    value="paced"
                    subtitle={
                      <small>
                        Counts pre- and post-Checkpoint activity separately
                      </small>
                    }
                  >
                    Paced grades
                  </RadioGroup.Radio>
                </RadioGroup>
              </div>
              {pacedControls}
              <div className="border-b" />
            </>
          )}
          <div>
            <h3 id={gradingTypeId} className="font-semibold mb-1">
              Grading type
            </h3>
            <RadioGroup
              data-testid="grading-type-radio-group"
              aria-labelledby={gradingTypeId}
              selected={gradingType}
              onChange={gradingType =>
                updateConfig({ grading_type: gradingType })
              }
            >
              <RadioGroup.Radio
                value="scaled"
                subtitle={<small>3 annotations out of 4 is 75%</small>}
              >
                Proportional
              </RadioGroup.Radio>
              <RadioGroup.Radio
                value="all_or_nothing"
                subtitle={<small>3 annotations out of 4 is 0%</small>}
              >
                All or nothing
              </RadioGroup.Radio>
            </RadioGroup>
          </div>
          <div>
            <h3 id={activityCalculationId} className="font-semibold mb-1">
              Activity calculation
            </h3>
            <RadioGroup
              data-testid="activity-calculation-radio-group"
              aria-labelledby={activityCalculationId}
              selected={activityCalculation}
              onChange={activityCalculation =>
                updateConfig({ activity_calculation: activityCalculation })
              }
            >
              <RadioGroup.Radio
                value="cumulative"
                subtitle={
                  <small>Annotations and replies tallied together.</small>
                }
              >
                Calculate cumulative
              </RadioGroup.Radio>
              <RadioGroup.Radio
                value="separate"
                subtitle={
                  <small>Annotations and replies tallied separately.</small>
                }
              >
                Calculate separately
              </RadioGroup.Radio>
            </RadioGroup>
          </div>
          {showPhases && (
            <TabList classes="gap-x-1">
              {gradingPhases.map((phase, index) => (
                <Tab
                  key={phase.label}
                  id={`${phasesId}-tab-${index}`}
                  // Only the phase on screen has a panel to point at: the
                  // others aren't rendered, so referencing them would be a
                  // dangling reference.
                  aria-controls={
                    index === activePhase ? `${phasesId}-panel` : undefined
                  }
                  data-testid={`phase-tab-${index}`}
                  variant="tab"
                  textContent={phase.label}
                  selected={index === activePhase}
                  onClick={() => setActivePhase(index)}
                >
                  {phase.label}
                  {/* The phase on screen never needs the pill: its empty input
                      says the same thing, right where you're looking. */}
                  {index !== activePhase &&
                    goalsAreUnset(phaseGoals[index]) && (
                      <span
                        data-testid={`phase-unset-${index}`}
                        className="ml-1.5 px-1.5 rounded-full border border-grey-5 text-xs font-normal text-grey-7 bg-white"
                      >
                        Not set
                      </span>
                    )}
                </Tab>
              ))}
            </TabList>
          )}
          {/* Within a paced assignment, both grading modes share this box; the
              only difference is the tab strip sitting on top of it. An
              assignment that can't be paced keeps the bare fields it has always
              had, so enabling paced grades changes nothing for everyone else. */}
          <div
            data-testid="goals-box"
            {...(showPhases
              ? {
                  role: 'tabpanel',
                  id: `${phasesId}-panel`,
                  'aria-labelledby': `${phasesId}-tab-${activePhase}`,
                }
              : {})}
            className={classnames(
              'flex flex-col gap-y-3',
              paced && 'p-3 border border-grey-3 rounded-lg',
              // Meet the selected tab, which has no bottom border of its own.
              showPhases && 'rounded-tl-none -mt-3',
            )}
          >
            {showPhases && (
              <h4
                data-testid="phase-description"
                className="uppercase text-xs font-semibold text-grey-7"
              >
                {gradingPhases[activePhase].description}
              </h4>
            )}
            <PhaseGoalsFields
              goals={showPhases ? phaseGoals[activePhase] : config.single}
              gradingType={gradingType}
              activityCalculation={activityCalculation}
              onChange={goals =>
                showPhases
                  ? updatePhaseGoals(activePhase, goals)
                  : updateConfig({ single: goals })
              }
            />
            {goalRefused && activeGoalsUnset && (
              <UIMessage
                status="error"
                role="alert"
                data-testid="phase-goal-error"
              >
                Set a goal for this phase.
              </UIMessage>
            )}
          </div>
        </>
      )}
    </div>
  );
}
