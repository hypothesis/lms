import type { ComponentChildren } from 'preact';

import type {
  AssignmentDetails,
  ISODateTime,
  StudentGradingSyncStatus,
  StudentWithMetrics,
} from '../../../api-types';
import type { OrderableActivityTableColumn } from '../OrderableActivityTable';

/**
 * The shape the students table takes for a given assignment.
 *
 * - `plain`: annotation metrics only, no grades.
 * - `auto-grading`: adds a `Grade` column with the currently calculated grade,
 *   and syncs those grades to the LMS.
 */
export type StudentsTableVariant = 'plain' | 'auto-grading';

/**
 * A row of the students table.
 *
 * `DataTable` and `useOrderedRows` index rows by `keyof Row`, so every value
 * the table displays has to live at the top level of the row.
 */
export type StudentsTableRow = {
  lms_id: string;
  h_userid: string;
  display_name: string | null;
  last_activity: string | null;
  annotations: number;
  replies: number;

  /** Currently calculated grade, only for auto-grading assignments */
  current_grade?: number;

  /**
   * Grade that was submitted to the LMS in the most recent sync.
   * If no grade has ever been synced, this will be `null`.
   * If the assignment is not auto-grading, this will be `undefined`.
   */
  last_grade?: number | null;

  /**
   * When the last grade sync happened, if any.
   * Not displayed in any column; it comes along with the rest of the grade.
   */
  last_grade_date?: ISODateTime | null;

  /** Whether this student is active in the course/assignment or roster */
  active: boolean;
};

/** A grade of a single student, as sent to the grades sync endpoint. */
export type GradeToSync = {
  h_userid: string;
  grade: number;
};

/**
 * Data a variant needs to decide its shape, beyond the students themselves.
 *
 * The whole assignment is passed rather than the specific fields a variant
 * reads, so that adding a variant which needs another field does not mean
 * touching the registry.
 */
export type VariantContext = {
  assignment?: AssignmentDetails | null;
};

/** Data a variant needs to render a cell, beyond the row itself. */
export type RenderContext = VariantContext & {
  /**
   * Status of the most recent grade sync, per student.
   *
   * A sync only covers the students whose grade changed, so a student with no
   * entry here has nothing in flight.
   */
  studentSyncStatuses: Partial<Record<string, StudentGradingSyncStatus>>;
};

/**
 * Everything which varies between two kinds of assignment in the students
 * table, in a single place.
 *
 * Adding support for a new kind of assignment means adding a module which
 * implements this and registering it, instead of spreading conditionals through
 * `AssignmentActivity`.
 */
export type StudentsTableVariantModule = {
  /** Identifies this variant in tests and debugging output. */
  variant: StudentsTableVariant;

  /** Flatten the API representation of the students into table rows. */
  buildRows(students: StudentWithMetrics[]): StudentsTableRow[];

  /**
   * Columns this variant displays, in display order.
   *
   * These depend on the assignment and nothing else: a variant which adds a
   * column group per grading window reads how many there are from it.
   */
  columns(
    context: VariantContext,
  ): OrderableActivityTableColumn<StudentsTableRow>[];

  /** Render one cell of a row. */
  renderItem(
    row: StudentsTableRow,
    field: keyof StudentsTableRow,
    context: RenderContext,
  ): ComponentChildren;

  /**
   * Grades to send to the LMS on the next sync.
   *
   * A variant which does not define this does not grade: the sync button is not
   * displayed and the status of the last sync is never polled. Leaving it out
   * is therefore the safe default for a new variant.
   */
  gradesToSync?(students: StudentWithMetrics[]): GradeToSync[];
};

/**
 * A variant which only handles the assignments exposing a given capability.
 *
 * These are the modules the registry chooses between. The variant which handles
 * everything the others do not claim is the registry's fallback, and therefore
 * does not need to match anything.
 */
export type ConditionalVariantModule = StudentsTableVariantModule & {
  /**
   * Whether this variant handles the given assignment.
   *
   * This is driven by the data the API returns rather than by explicit flags,
   * so that an assignment which does not have a given capability simply falls
   * through to a more basic variant.
   */
  matches(assignment?: AssignmentDetails | null): boolean;
};

/** What the students table needs to be rendered, for one assignment. */
export type StudentsTableConfig = {
  rows: StudentsTableRow[];
  columns: OrderableActivityTableColumn<StudentsTableRow>[];
  renderItem: (
    row: StudentsTableRow,
    field: keyof StudentsTableRow,
  ) => ComponentChildren;
};
