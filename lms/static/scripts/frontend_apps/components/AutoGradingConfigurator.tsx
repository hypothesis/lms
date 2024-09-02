import {
  Checkbox,
  CheckboxCheckedFilledIcon,
  Input,
  RadioGroup,
} from '@hypothesis/frontend-shared';
import type { ComponentChildren } from 'preact';
import { useCallback, useId } from 'preact/hooks';

export type GradingType = 'all_or_nothing' | 'scaled';

export type AutoGradingConfig = {
  /** Whether auto grading is enabled for the assignment or not */
  enabled?: boolean;

  /**
   * - all_or_nothing: students need to meet a minimum value, making them get
   *                   either 0% or 100%
   * - scaled: students may get a proportional grade based on the amount of
   *           annotations. If requirement is 4, and they created 3, they'll
   *           get a 75%
   */
  gradingType: GradingType;

  /**
   * - cumulative: both annotations and replies will be counted together for
   *               the grade calculation
   * - separate: students will have different annotation and reply goals.
   */
  activityCalculation: 'cumulative' | 'separate';

  /**
   * Required number of annotations if activityCalculation is 'separate' or
   * combined number of annotations and replies otherwise.
   */
  requiredAnnotations: number;

  /**
   * Required number of replies if activityCalculation is 'separate'
   */
  requiredReplies?: number;
};

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

export type AutoGradingConfiguratorProps = {
  config: AutoGradingConfig;
  onChange: (newConfig: AutoGradingConfig) => void;
};

/**
 * Allows instructors to enable auto grading for an assignment, and provide the
 * configuration to determine how to calculate each student's grade.
 */
export default function AutoGradingConfigurator({
  config,
  onChange,
}: AutoGradingConfiguratorProps) {
  const {
    enabled = false,
    gradingType,
    activityCalculation,
    requiredAnnotations,
    requiredReplies = 0,
  } = config;
  const updateConfig = useCallback(
    (newConfig: Partial<AutoGradingConfig>) =>
      onChange({ ...config, ...newConfig }),
    [config, onChange],
  );

  const gradingTypeId = useId();
  const activityCalculationId = useId();

  return (
    <div className="flex flex-col gap-y-3">
      <Checkbox
        checked={enabled}
        checkedIcon={CheckboxCheckedFilledIcon}
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
          <div>
            <h3 id={gradingTypeId} className="font-semibold mb-1">
              Grading type
            </h3>
            <RadioGroup
              data-testid="grading-type-radio-group"
              aria-labelledby={gradingTypeId}
              selected={gradingType}
              onChange={gradingType => updateConfig({ gradingType })}
            >
              <RadioGroup.Radio
                value="all_or_nothing"
                subtitle={<small>Must meet minimum requirements.</small>}
              >
                All or nothing
              </RadioGroup.Radio>
              <RadioGroup.Radio
                value="scaled"
                subtitle={<small>Proportional to percent completed.</small>}
              >
                Scaled
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
                updateConfig({ activityCalculation })
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
          <AnnotationsGoalInput
            gradingType={gradingType}
            value={requiredAnnotations}
            onChange={requiredAnnotations =>
              updateConfig({ requiredAnnotations })
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
              onChange={requiredReplies => updateConfig({ requiredReplies })}
              min={0}
            >
              Replies
            </AnnotationsGoalInput>
          )}
        </>
      )}
    </div>
  );
}
