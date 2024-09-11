import { CheckIcon, CancelIcon } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { ComponentChildren } from 'preact';
import { useCallback, useState } from 'preact/hooks';

import type { AutoGradingConfig } from '../../api-types';
import GradeStatusChip from './GradeStatusChip';

type AnnotationCountProps = {
  children: ComponentChildren;
  actualAmount: number;
  requiredAmount: number;
};

function AnnotationCount({
  children,
  actualAmount,
  requiredAmount,
}: AnnotationCountProps) {
  const requirementWasMet = actualAmount >= requiredAmount;

  return (
    <div
      className={classnames(
        'flex justify-between items-center gap-x-3',
        'border-b last:border-0 px-3 py-2.5',
      )}
    >
      <div className="flex items-center gap-x-2">
        {children}
        <div className="px-2 py-1 rounded bg-grey-3 text-grey-7 font-bold">
          {actualAmount}/{requiredAmount}
        </div>
      </div>
      <div
        className={classnames('rounded-full p-1', {
          'bg-grade-success-light text-grade-success': requirementWasMet,
          'bg-grade-error-light text-grade-error': !requirementWasMet,
        })}
      >
        {requirementWasMet ? <CheckIcon /> : <CancelIcon />}
      </div>
    </div>
  );
}

export type GradeIndicatorProps = {
  grade: number;
  annotations: number;
  replies: number;
  config?: AutoGradingConfig;
};

/**
 * Includes a GradeStatusChip, together with a popover indicating why that is
 * the grade
 */
export default function GradeIndicator({
  grade,
  annotations,
  replies,
  config,
}: GradeIndicatorProps) {
  const [popoverVisible, setPopoverVisible] = useState(false);
  const showPopover = useCallback(() => setPopoverVisible(true), []);
  const hidePopover = useCallback(() => setPopoverVisible(false), []);

  const isCalculationSeparate = config?.activity_calculation === 'separate';
  const combined = annotations + replies;
  const requiredCombined = config
    ? config.required_annotations + (config.required_replies ?? 0)
    : 0;

  return (
    <div
      className="inline-block relative"
      onMouseOver={showPopover}
      onMouseOut={hidePopover}
      // Make element focusable so that the popover can be shown even when
      // interacting with the keyboard
      onFocus={showPopover}
      onBlur={hidePopover}
      role="button"
      tabIndex={0}
      data-testid="container"
    >
      <GradeStatusChip grade={grade} />
      <div aria-live="polite" aria-relevant="additions">
        {popoverVisible && (
          <div
            role="tooltip"
            className={classnames(
              'rounded shadow-lg bg-white border',
              'w-64 absolute -left-6 top-full mt-0.5',
            )}
            data-testid="popover"
          >
            <div className="border-b px-3 py-2 font-bold text-grey-7">
              Grade calculation
            </div>
            {isCalculationSeparate && (
              <AnnotationCount
                actualAmount={annotations}
                requiredAmount={config.required_annotations}
              >
                Annotations
              </AnnotationCount>
            )}
            {isCalculationSeparate ? (
              <AnnotationCount
                actualAmount={replies}
                requiredAmount={config.required_replies ?? 0}
              >
                Replies
              </AnnotationCount>
            ) : (
              <AnnotationCount
                actualAmount={combined}
                requiredAmount={requiredCombined}
              >
                Annotations and replies
              </AnnotationCount>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
