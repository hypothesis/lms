import {
  CheckIcon,
  CancelIcon,
  useKeyPress,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { ComponentChildren } from 'preact';
import { useCallback, useId, useState } from 'preact/hooks';

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

function SectionTitle({ children }: { children: ComponentChildren }) {
  return (
    <div className="border-b px-3 py-2 font-bold text-grey-7">{children}</div>
  );
}

export type GradeIndicatorProps = {
  grade: number;
  lastGrade?: number | null;
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
  lastGrade,
  annotations,
  replies,
  config,
}: GradeIndicatorProps) {
  const [popoverVisible, setPopoverVisible] = useState(false);
  const showPopover = useCallback(() => setPopoverVisible(true), []);
  const hidePopover = useCallback(() => setPopoverVisible(false), []);
  const popoverId = useId();

  useKeyPress(['Escape'], hidePopover);

  const isCalculationSeparate = config?.activity_calculation === 'separate';
  const combined = annotations + replies;
  const requiredCombined = config
    ? config.required_annotations + (config.required_replies ?? 0)
    : 0;
  // Checking typeof lastGrade to avoid number zero to be treated as false
  const hasLastGrade = typeof lastGrade === 'number';
  const gradeHasChanged = lastGrade !== grade;

  return (
    <div className="relative">
      <div className="flex items-center justify-between">
        <button
          className="focus-visible-ring rounded"
          onClick={showPopover}
          onMouseOver={showPopover}
          onFocus={showPopover}
          onMouseOut={hidePopover}
          onBlur={hidePopover}
          data-testid="popover-toggle"
          aria-expanded={popoverVisible}
          aria-describedby={popoverVisible ? popoverId : undefined}
          aria-controls={popoverVisible ? popoverId : undefined}
        >
          <GradeStatusChip grade={grade} />
        </button>
        {gradeHasChanged && (
          <div
            data-testid="new-label"
            className={classnames(
              'px-1 py-0.5 rounded',
              'bg-grey-7 text-white font-bold uppercase text-[0.65rem]',
            )}
          >
            New
          </div>
        )}
      </div>
      <div aria-live="polite" aria-relevant="additions">
        {popoverVisible && (
          <div
            id={popoverId}
            className={classnames(
              'rounded shadow-lg bg-white border',
              'w-64 absolute z-1 -left-6 top-full mt-0.5',
            )}
            data-testid="popover"
          >
            {hasLastGrade && gradeHasChanged && (
              <>
                <SectionTitle>Previously synced grade</SectionTitle>
                <div className="border-b px-3 py-2" data-testid="last-grade">
                  <GradeStatusChip grade={lastGrade} />
                </div>
              </>
            )}
            <SectionTitle>Grade calculation</SectionTitle>
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
