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
import GradeStatusChip, { formatGrade } from './GradeStatusChip';
import type { StudentStatusType } from './StudentStatusBadge';
import StudentStatusBadge from './StudentStatusBadge';

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
          'bg-green-light text-green-dark': requirementWasMet,
          'bg-red-light text-red-dark': !requirementWasMet,
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

/** The activity a grade was calculated from, and the config it was graded by. */
type RequirementsProps = {
  annotations: number;
  replies: number;
  config?: AutoGradingConfig;
};

/** What the grade was calculated from, against what it needed. */
function Requirements({ annotations, replies, config }: RequirementsProps) {
  const isCalculationSeparate = config?.activity_calculation === 'separate';
  const requiredCombined = config
    ? config.required_annotations + (config.required_replies ?? 0)
    : 0;

  return (
    <>
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
          actualAmount={annotations + replies}
          requiredAmount={requiredCombined}
        >
          Annotations and replies
        </AnnotationCount>
      )}
    </>
  );
}

/** A grade the table displays, whichever indicator displays it. */
type GradeProps = {
  grade: number;
  lastGrade?: number | null;
  status?: StudentGradingSyncStatus;
};

export type GradeIndicatorProps = GradeProps &
  RequirementsProps & {
    /**
     * Whether this is the grade the LMS gets.
     *
     * A phase's own grade is informational -- only the final one is ever
     * synced -- so it carries no sync state to report, and none of the colour
     * which says how the assignment is going.
     */
    synced?: boolean;
  };

type GradeHoverProps = GradeProps & {
  synced?: boolean;

  /** What the reader hovers: the grade, however it is displayed. */
  trigger: ComponentChildren;

  /** What the popover explains about it. */
  children: ComponentChildren;
};

/** A grade, with a popover explaining it on hover or focus. */
function GradeHover({
  grade,
  lastGrade,
  status,
  synced = true,
  trigger,
  children,
}: GradeHoverProps) {
  const [popoverVisible, setPopoverVisible] = useState(false);
  const showPopover = useCallback(() => setPopoverVisible(true), []);
  const hidePopover = useCallback(() => setPopoverVisible(false), []);
  const popoverId = useId();

  useKeyPress(['Escape'], hidePopover);

  // Checking typeof lastGrade to avoid number zero to be treated as false
  const hasLastGrade = typeof lastGrade === 'number';
  const gradeHasChanged = lastGrade !== grade;
  const badgeType = ((): StudentStatusType | undefined => {
    if (!synced) {
      return undefined;
    }
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
          {trigger}
        </button>
        {badgeType && <StudentStatusBadge type={badgeType} />}
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
            {hasLastGrade && gradeHasChanged && synced && (
              <>
                <SectionTitle>Previously synced grade</SectionTitle>
                <div className="border-b px-3 py-2" data-testid="last-grade">
                  <GradeStatusChip grade={lastGrade} />
                </div>
              </>
            )}
            <SectionTitle>Grade calculation</SectionTitle>
            {children}
          </div>
        )}
      </div>
    </div>
  );
}

/** A grade, with a popover listing the requirements behind it. */
export default function GradeIndicator({
  grade,
  lastGrade,
  annotations,
  replies,
  config,
  status,
  synced = true,
}: GradeIndicatorProps) {
  return (
    <GradeHover
      grade={grade}
      lastGrade={lastGrade}
      status={status}
      synced={synced}
      trigger={<GradeStatusChip grade={grade} muted={!synced} />}
    >
      <Requirements
        annotations={annotations}
        replies={replies}
        config={config}
      />
    </GradeHover>
  );
}

/**
 * One line of the final grade's summary: what a phase, or the average, scored.
 *
 * A phase which has not started is greyed out and scores a dash rather than a
 * zero: nothing was possible in it yet, so it has not failed its requirements.
 */
function SummaryRow({
  children,
  grade,
  total = false,
}: {
  children: ComponentChildren;
  grade?: number;
  total?: boolean;
}) {
  const started = grade !== undefined;

  return (
    <div
      className={classnames(
        'flex justify-between items-center gap-x-3',
        'border-b last:border-0 px-3 py-2.5',
        { 'font-bold': total, 'text-grey-5': !started },
      )}
    >
      <div>{children}</div>
      <div>{started ? `${formatGrade(grade)}%` : '—'}</div>
    </div>
  );
}

/**
 * What one phase contributed to the final grade.
 *
 * A phase still to come has no grade: it is listed all the same, because this
 * summary is the only place the reader can see that the average does not cover
 * the whole assignment yet.
 */
export type GradeContribution = {
  label: string;
  grade?: number;
};

export type FinalGradeIndicatorProps = GradeProps & {
  /** The phases the grade is the average of, in display order. */
  phases: GradeContribution[];
};

/**
 * The grade the LMS gets, and what each phase contributed to it.
 *
 * The only coloured grade on the row: it is the one the gradebook receives, and
 * the phases it averages are shown in grey.
 *
 * Every phase is listed, the ones still to come included, which is what keeps
 * the average from reading as a settled one: before the first reveal it sits
 * under a phase with no grade of its own yet.
 */
export function FinalGradeIndicator({
  grade,
  lastGrade,
  status,
  phases,
}: FinalGradeIndicatorProps) {
  return (
    <GradeHover
      grade={grade}
      lastGrade={lastGrade}
      status={status}
      trigger={<GradeStatusChip grade={grade} />}
    >
      {phases.map(({ label, grade: phaseGrade }) => (
        <SummaryRow key={label} grade={phaseGrade}>
          {label}
        </SummaryRow>
      ))}
      {phases.length > 0 && (
        <SummaryRow grade={grade} total>
          Average
        </SummaryRow>
      )}
    </GradeHover>
  );
}
