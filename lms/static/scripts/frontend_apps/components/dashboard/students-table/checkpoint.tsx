import type { ComponentChildren } from 'preact';

import type { StudentWithMetrics } from '../../../api-types';
import type { GradeContribution, GradePhase } from '../GradeIndicator';
import GradeIndicator, { FinalGradeIndicator } from '../GradeIndicator';
import type { OrderableActivityTableColumn } from '../OrderableActivityTable';
import {
  gradeColumn,
  gradesToSync,
  renderAutoGradingField,
} from './auto-grading';
import {
  buildRows,
  lastActivityColumn,
  metricsColumns,
  renderSharedField,
  studentColumn,
} from './shared';
import type {
  AnyStudentsTableRow,
  ConditionalVariantModule,
  RenderContext,
  StudentsTableRow,
  VariantContext,
} from './types';

/** A grading phase of a checkpoint assignment, as a group of columns. */
export type CheckpointPhase = {
  /** 1-based position, the one the API reports. */
  phase: number;

  /** Header the metrics of this phase are displayed under. */
  label: string;
};

/** Metrics a phase displays, in display order within its group. */
const PHASE_METRICS = ['grade', 'annotations', 'replies'] as const;

type PhaseMetric = (typeof PHASE_METRICS)[number];

const METRIC_LABELS: Record<PhaseMetric, string> = {
  grade: 'Grade',
  annotations: 'Annotations',
  replies: 'Replies',
};

/**
 * Field a metric of a phase is stored under, in a row.
 *
 * Rows and columns both derive their fields from here, so they cannot drift
 * apart: a phase which the API does not report produces neither.
 */
export function metricKey(phase: number, metric: PhaseMetric): string {
  return `phase_${phase}_${metric}`;
}

/** Matches the fields {@link metricKey} generates, capturing the metric. */
const PHASE_FIELD = new RegExp(`^phase_(\\d+)_(${PHASE_METRICS.join('|')})$`);

/**
 * Phases an assignment with checkpoints has at the very least.
 *
 * A checkpoint splits the activity in two, and the MVP has exactly one, so an
 * assignment which reports any phase has two. This is what keeps the last phase
 * from being guessed wrong while nobody has been active in it yet: the day after
 * a reveal, the API only reports phase 1, and calling that one the revealed
 * phase would be wrong.
 *
 * ⚠️ This makes the labels correct for **one** checkpoint and only that. With
 * two, the API reports phases 1 and 2 until somebody is active in the third, and
 * phase 2 gets labelled as the revealed one. There is no way around it from
 * here: the API reports the position of a phase and never how many the
 * assignment has.
 *
 * @todo Two things fix this for good, both on the API: reporting the phases of
 * the assignment (the per-phase auto-grading configs already exist in the
 * backend), or reporting an entry per defined phase for every student, zeros
 * included.
 */
const MIN_PHASES = 2;

/**
 * Header a phase is displayed under.
 *
 * The API reports the position of a phase, not a name. Annotations stay hidden
 * until the checkpoint before them is revealed, so every phase but the last is
 * a hidden one and the last is what the reveal opens up. Naming them that way
 * rather than after the due date also suits an assignment which has none.
 *
 * Numbering by position rather than by how many phases came back keeps the
 * labels in order and distinct, which the grouped header needs: two adjacent
 * columns declaring the same group are displayed under a single header.
 */
function phaseLabel(phase: number, lastPhase: number): string {
  if (phase === lastPhase) {
    return 'Revealed Phase';
  }

  // Numbered only when there is more than one to tell apart.
  return lastPhase > 2 ? `Hidden Phase ${phase}` : 'Hidden Phase';
}

/**
 * Phases these students report, in order.
 *
 * The phases are read off the students rather than off the assignment because
 * that is where the API reports them, and it is what makes the table degrade on
 * its own: an assignment whose activity is not split yet reports none, and the
 * table falls back to the totals.
 */
function phasesOf(students: StudentWithMetrics[]): CheckpointPhase[] {
  const positions = new Set<number>();
  for (const { phase_metrics } of students) {
    for (const { phase } of phase_metrics ?? []) {
      positions.add(phase);
    }
  }

  const ordered = [...positions].sort((a, b) => a - b);
  // The API only reports the phases a student was active in, so the highest one
  // reported is not necessarily the last one the assignment has.
  const lastPhase = Math.max(MIN_PHASES, ...ordered);

  return ordered.map(phase => ({
    phase,
    label: phaseLabel(phase, lastPhase),
  }));
}

/**
 * A row of the students table of a checkpoint assignment.
 *
 * The metrics of each phase live at the top level under a generated key, which
 * is why this is the wide row shape: see {@link AnyStudentsTableRow}. The cost
 * is that the compiler can no longer catch a typo in a column's `field`, and
 * generating every key through {@link metricKey} is what replaces it.
 */
export type CheckpointRow = AnyStudentsTableRow;

/** Flatten the metrics of every phase into a single row per student. */
export function buildCheckpointRows(
  students: StudentWithMetrics[],
): CheckpointRow[] {
  const phases = phasesOf(students);
  // Keyed by student rather than zipped by position: a row which took its
  // phases from the wrong student would show its grades under another name, and
  // nothing would fail.
  const metricsOf = new Map(
    students.map(({ h_userid, phase_metrics }) => [
      h_userid,
      new Map((phase_metrics ?? []).map(entry => [entry.phase, entry])),
    ]),
  );

  return buildRows(students).map(row => {
    const byPhase = metricsOf.get(row.h_userid) ?? new Map();
    const phaseFields: Record<string, number | undefined> = {};

    for (const { phase } of phases) {
      const entry = byPhase.get(phase);
      phaseFields[metricKey(phase, 'annotations')] = entry?.metrics.annotations;
      phaseFields[metricKey(phase, 'replies')] = entry?.metrics.replies;
      phaseFields[metricKey(phase, 'grade')] = entry?.grade;
    }

    return { ...row, ...phaseFields };
  });
}

/**
 * Columns of a checkpoint assignment: the same metrics repeated once per phase,
 * each under the header of its phase.
 *
 * A phase no student reports is not displayed, which is also what the product
 * contract asks for: a section which is not defined gets no column. While no
 * phase is reported at all — which is the case until the backend splits the
 * activity — this is exactly the table the assignment would display without
 * checkpoints, rather than a grid of empty cells.
 *
 * Grades are only displayed for an assignment which is also auto-graded, so a
 * checkpoint assignment without grading shows the same groups with two columns
 * instead of three.
 */
export function checkpointColumns(
  { students }: VariantContext,
  { grades }: { grades: boolean },
): OrderableActivityTableColumn<CheckpointRow>[] {
  const phases = phasesOf(students ?? []);

  if (phases.length === 0) {
    return [studentColumn, ...(grades ? [gradeColumn] : []), ...metricsColumns];
  }

  const displayed = PHASE_METRICS.filter(
    metric => grades || metric !== 'grade',
  );

  return [
    // Wide enough for a student name on one line, and no wider: the metrics
    // divide what is left, and their `Annotations` header needs every pixel of
    // its share. The flat table reserves far more, but it has four columns.
    { ...studentColumn, width: 'w-44' },
    ...phases.flatMap(({ phase, label }) =>
      displayed.map(metric => ({
        field: metricKey(phase, metric),
        label: METRIC_LABELS[metric],
        group: label,
        ...(metric === 'grade'
          ? {}
          : { initialOrderDirection: 'descending' as const }),
      })),
    ),
    ...(grades ? [{ ...gradeColumn, group: 'Final grade' }] : []),
    // A formatted date does not wrap, and an even share of a table this wide is
    // not enough for one: with a phase per checkpoint there are at least six
    // other columns to divide the rest between.
    { ...lastActivityColumn, width: 'w-40' },
  ];
}

/**
 * The phases the final grade is made of, for its popover.
 *
 * Read off the student rather than the row: the popover needs each phase's own
 * counts and requirements together, and a row holds one value per cell. Only
 * the phases which contributed are listed, so an unstarted or ungraded one
 * isn't shown as having failed its requirement.
 */
function gradePhases(
  row: CheckpointRow,
  { students }: RenderContext,
  /** Limit to one phase, for the breakdown of that phase's own grade. */
  position?: number,
): GradePhase[] {
  const student = students?.find(({ h_userid }) => h_userid === row.h_userid);
  const labels = new Map(
    phasesOf(students ?? []).map(({ phase, label }) => [phase, label]),
  );

  return (student?.phase_metrics ?? [])
    .filter(({ phase, started, requirements }) => {
      if (position !== undefined) {
        return phase === position && requirements;
      }

      return started && requirements;
    })
    .map(({ phase, metrics, requirements }) => ({
      // The heading names which phase a section is for, which the breakdown of
      // a single one does not need: the cell being hovered says so already.
      label: position === undefined ? labels.get(phase) : undefined,
      annotations: metrics.annotations,
      replies: metrics.replies,
      config: requirements,
    }));
}

/**
 * What each phase contributed to the final grade, phases still to come
 * included.
 *
 * A phase nobody has reached has no columns of its own, so this summary is the
 * only place the reader can see one is still outstanding -- and so the only
 * place that says the average is not over the whole assignment yet. Which
 * phases the assignment has is the same assumption the headers make: see
 * {@link MIN_PHASES}.
 *
 * Nothing is listed while the activity is not split at all, which is when the
 * table displays the totals and this is the only grade there is.
 */
function gradeContributions(
  row: CheckpointRow,
  { students }: RenderContext,
): GradeContribution[] {
  const reported = phasesOf(students ?? []);
  if (reported.length === 0) {
    return [];
  }

  const student = students?.find(({ h_userid }) => h_userid === row.h_userid);
  const byPhase = new Map(
    (student?.phase_metrics ?? []).map(entry => [entry.phase, entry]),
  );
  const lastPhase = Math.max(MIN_PHASES, ...reported.map(({ phase }) => phase));

  return Array.from({ length: lastPhase }, (_, index) => {
    const entry = byPhase.get(index + 1);

    return {
      label: phaseLabel(index + 1, lastPhase),
      // A phase which has not started, or which has no requirements of its
      // own, contributed nothing and is shown as outstanding rather than as a
      // zero -- the same phases `_final_grade` leaves out of the average.
      grade: entry?.started && entry.requirements ? entry.grade : undefined,
    };
  });
}

/**
 * Render a cell of a checkpoint row.
 *
 * A metric of a phase is rendered here; everything else falls back to the
 * variant this one extends, so the student, final grade and last activity
 * columns look exactly like they do in the other tables.
 */
export function renderCheckpointField(
  row: CheckpointRow,
  field: keyof CheckpointRow,
  { grades, context }: { grades: boolean; context: RenderContext },
): ComponentChildren {
  const name = String(field);
  const phaseMetric = PHASE_FIELD.exec(name);

  if (!phaseMetric) {
    const sharedField = field as keyof StudentsTableRow;

    if (grades && sharedField === 'current_grade') {
      const contributions = gradeContributions(row, context);

      // Without phases the table displays the totals, and the grade is the
      // assignment's own requirements met once: the flat renderer explains it.
      if (contributions.length === 0) {
        return renderAutoGradingField(row, sharedField, context);
      }

      // Only this grade reaches the LMS, so it keeps the colour and the sync
      // badge; the popover names what each phase contributed and their average.
      return (
        <div className="flex justify-end -my-0.5">
          <FinalGradeIndicator
            grade={row.current_grade ?? 0}
            lastGrade={row.last_grade}
            status={context.studentSyncStatuses[row.h_userid]}
            phases={contributions}
          />
        </div>
      );
    }

    return renderSharedField(row, sharedField);
  }

  const value = row[name];
  if (value === undefined || value === null) {
    return '';
  }

  const [, position, metric] = phaseMetric;

  if (metric === 'grade') {
    // The same indicator as the final grade, so hovering a phase's grade
    // breaks it down the way hovering the final one breaks down every phase.
    // `synced` is off: only the final grade reaches the LMS, so this one is
    // grey and carries no badge.
    return (
      <div className="flex justify-end -my-0.5">
        <GradeIndicator
          grade={Number(value)}
          phases={gradePhases(row, context, Number(position))}
          synced={false}
        />
      </div>
    );
  }

  return <div className="text-right">{value}</div>;
}

/**
 * Metrics of a Hide & Reveal assignment, split by grading phase.
 *
 * An assignment which is not also auto-graded displays no grade at all, so this
 * variant does not sync anything to the LMS.
 */
export const checkpointVariant: ConditionalVariantModule<CheckpointRow> = {
  variant: 'checkpoint',
  handles: ['checkpoints'],
  buildRows: buildCheckpointRows,
  columns: context => checkpointColumns(context, { grades: false }),
  renderItem: (row, field, context) =>
    renderCheckpointField(row, field, { grades: false, context }),
};

/**
 * Metrics and grades of a Hide & Reveal assignment, split by grading phase.
 *
 * Only the final grade is synced to the LMS: the grade of a phase is displayed
 * so that the teacher can see how it was reached, but the LMS gradebook has a
 * single grade per assignment.
 */
export const checkpointAutoGradingVariant: ConditionalVariantModule<CheckpointRow> =
  {
    variant: 'checkpoint-auto-grading',
    handles: ['checkpoints', 'auto-grading'],
    buildRows: buildCheckpointRows,
    columns: context => checkpointColumns(context, { grades: true }),
    renderItem: (row, field, context) =>
      renderCheckpointField(row, field, { grades: true, context }),
    gradesToSync,
  };
