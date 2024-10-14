import {
  CheckIcon,
  CancelIcon,
  useKeyPress,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { ComponentChildren } from 'preact';
import { useCallback, useId, useState } from 'preact/hooks';

import type {
  AutoGradingConfig,
  StudentGradingSyncStatus,
} from '../../api-types';
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

type BadgeType = 'new' | 'error' | 'syncing';

function Badge({ type }: { type: BadgeType }) {
  return (
    <div
      className={classnames(
        'px-1 py-0.5 rounded cursor-auto font-bold uppercase text-[0.65rem]',
        {
          'bg-grey-7 text-white': type === 'new',
          'bg-grade-error-light text-grade-error': type === 'error',
          'bg-grey-2 text-grey-7': type === 'syncing',
        },
      )}
    >
      {type === 'new' && 'New'}
      {type === 'error' && 'Error'}
      {type === 'syncing' && 'Syncing'}
    </div>
  );
}

export type GradeIndicatorProps = {
  grade: number;
  lastGrade?: number | null;
  annotations: number;
  replies: number;
  status?: StudentGradingSyncStatus;
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
  status,
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
  const badgeType = ((): BadgeType | undefined => {
    if (status === 'in_progress') {
      return 'syncing';
    }
    if (status === 'failed') {
      return 'error';
    }

    return gradeHasChanged ? 'new' : undefined;
  })();

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
        {badgeType && <Badge type={badgeType} />}
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
