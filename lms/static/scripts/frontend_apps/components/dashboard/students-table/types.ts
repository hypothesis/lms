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
 * - `checkpoint`: repeats the metrics once per window of a Hide & Reveal
 *   assignment, each under the header of its window.
 * - `checkpoint-auto-grading`: the windows of `checkpoint` plus a grade per
 *   window and a final grade, which is the one synced to the LMS.
 *
 * The two checkpoint variants exist separately because whether an assignment
 * grades is not something a single module can decide: `gradesToSync` is what
 * gates the sync button, and it is read off the module rather than called.
 */
export type StudentsTableVariant =
  | 'plain'
  | 'auto-grading'
  | 'checkpoint'
  | 'checkpoint-auto-grading';

/**
 * Something an assignment can do, which changes the shape of its table.
 *
 * A capability is detected from the data the API returns rather than from an
 * explicit flag, in one place in the registry. A variant declares which ones it
 * handles and never inspects the assignment itself.
 */
export type AssignmentCapability = 'auto-grading' | 'checkpoints';

/**
 * A row of the students table, for the variants which display a single set of
 * annotation metrics per student.
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

/**
 * Row of a variant which generates part of its fields at runtime.
 *
 * `useOrderedRows` indexes rows by `keyof Row`, so a variant which repeats a
 * metric once per window has to put those values at the top level under a
 * generated key. This is the shape the registry holds, so that such a variant
 * can sit next to the ones whose fields are all known.
 *
 * A variant with a fixed set of fields should use {@link StudentsTableRow}
 * instead and keep its columns checked by the compiler.
 */
export type AnyStudentsTableRow = StudentsTableRow & {
  [generatedField: string]: string | number | boolean | null | undefined;
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

  /**
   * The students the table is about to display, or `undefined` while they load.
   *
   * A variant whose columns depend on which data the students actually report
   * reads them from here: `columns` is resolved before the rows are rendered,
   * so it has no other way to see them.
   */
  students?: StudentWithMetrics[];
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
export type StudentsTableVariantModule<
  Row extends StudentsTableRow = StudentsTableRow,
> = {
  /** Identifies this variant in tests and debugging output. */
  variant: StudentsTableVariant;

  /** Flatten the API representation of the students into table rows. */
  buildRows(students: StudentWithMetrics[]): Row[];

  /**
   * Columns this variant displays, in display order.
   *
   * These depend on the assignment and nothing else: a variant which adds a
   * column group per grading window reads how many there are from it.
   */
  columns(context: VariantContext): OrderableActivityTableColumn<Row>[];

  /** Render one cell of a row. */
  renderItem(
    row: Row,
    field: keyof Row,
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
 * declares nothing.
 */
export type ConditionalVariantModule<
  Row extends StudentsTableRow = StudentsTableRow,
> = StudentsTableVariantModule<Row> & {
  /**
   * Capabilities of an assignment this variant handles.
   *
   * A variant owns the assignments whose capabilities are exactly these, which
   * is what keeps two variants from claiming the same assignment: the sets are
   * distinct by construction, so adding a variant never means excluding its
   * capability from the variants which came before it.
   */
  handles: AssignmentCapability[];
};

/** What the students table needs to be rendered, for one assignment. */
export type StudentsTableConfig<
  Row extends StudentsTableRow = StudentsTableRow,
> = {
  rows: Row[];
  columns: OrderableActivityTableColumn<Row>[];
  renderItem: (row: Row, field: keyof Row) => ComponentChildren;
};
