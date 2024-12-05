/**
 * Types for objects exchanged between the LMS frontend and backend via
 * JSON HTTP requests.
 */
import type { APICallInfo } from './config';

/**
 * MIME types which are recognized by the frontend.
 *
 * These are used to choose appropriate icons to represent the file.
 */
export type MimeType = 'text/html' | 'application/pdf' | 'video';

/**
 * Object representing a file or folder in cloud storage.
 */
export type FileBase = {
  type: 'File' | 'Folder';

  /** Identifier for the document within the LMS. */
  id: string;

  /** Name of the file or folder. */
  display_name: string;

  /** An ISO 8601 date string. */
  updated_at?: string;
};

export type File = FileBase & {
  type: 'File';

  /**
   * MIME type of the file.
   *
   * This can either be a top-level type (eg. "video", "text") or a sub-type
   * ("text/html").
   */
  mime_type?: MimeType;

  /** URL of a thumbnail for this item. */
  thumbnail_url?: string;

  /** Duration of audio or video in seconds. */
  duration?: number;
};

export type Folder = FileBase & {
  type: 'Folder';

  /**
   * Details of an API call to fetch the folder's children.
   *
   * Either this property or {@link FileBase.children} will be used to provide
   * the children, depending on whether the backend decides to require a
   * separate API call to fetch children or not.
   */
  contents?: APICallInfo;

  /** ID of the parent folder. */
  parent_id?: string | null;

  /** Children of this folder. See {@link FileBase.contents}. */
  children?: Array<File | Folder>;
};

/**
 * Object representing a set of groups that students can be divided into for
 * an assignment.
 */
export type GroupSet = {
  id: string;
  name: string;
};

/** Metadata for an ebook that is available to annotate. */
export type Book = {
  id: string;
  title: string;
  /** URL of a cover image for the book. */
  cover_image: string;
};

/**
 * Metadata for a table of contents entry within an ebook.
 *
 * The name "Chapter" is a misnomer. Although many ebooks do have one
 * table-of-contents entry per chapter, the entries can be more or less
 * fine-grained than this.
 */
export type TableOfContentsEntry = {
  page: string;
  title: string;

  /** EPUB CFI of this chapter. */
  cfi: string;

  /** Document URL to use for this chapter when creating an assignment. */
  url: string;

  /**
   * The nesting depth of this entry in the table of contents.
   */
  level?: number;
};

export type JSTORContentItemInfo = {
  title: string;
  subtitle?: string;
};

export type JSTORRelatedItemsInfo = {
  next_id?: string;
  previous_id?: string;
};

/**
 * Response for an `/api/jstor/articles/{article_id}` call.
 */
export type JSTORMetadata = {
  content_status: 'available' | 'no_content' | 'no_access';
  item: JSTORContentItemInfo;
  container: JSTORContentItemInfo;
  related_items: JSTORRelatedItemsInfo;
};

/**
 * Response for an `/api/jstor/articles/{article_id}/thumbnail` call.
 */
export type JSTORThumbnail = {
  image: string;
};

export type YouTubeVideoRestriction = 'age' | 'no_embed';

/**
 * Response for an `/api/youtube/videos/{video_id}` call.
 */
export type YouTubeVideoInfo = {
  title: string;
  channel: string;
  image: string;
  restrictions: YouTubeVideoRestriction[];
};

/*
 * Dashboard-related API types
 */

/**
 * Represents dates exposed by the backend as string, in ISO 8601 format
 */
export type ISODateTime = string;

export type AnnotationMetrics = {
  last_activity: ISODateTime | null;
  annotations: number;
  replies: number;
};

/**
 * Response for `/api/dashboard/courses/{course_id}` call.
 */
export type Course = {
  id: number;
  title: string;
};

export type CourseMetrics = {
  assignments: number;
  last_launched: ISODateTime | null;
};

export type CourseWithMetrics = Course & {
  course_metrics: CourseMetrics;
};

/**
 * Response for `/api/dashboard/course/metrics` call.
 */
export type CoursesMetricsResponse = {
  courses: CourseWithMetrics[];
};

export type Assignment = {
  id: number;
  title: string;
  /** Date in which the assignment was created, in ISO format */
  created: ISODateTime;
  is_gradable: boolean;
};

export type Student = {
  h_userid: string;
  lms_id: string;
  display_name: string | null;
};

export type AutoGradingGrade = {
  /** Grade calculated with current annotations/replies */
  current_grade: number;
  /** Grade that was last synced, if any */
  last_grade: number | null;
  /** When did the last grade sync happen, if any */
  last_grade_date: ISODateTime | null;
};

export type StudentWithMetrics = Student & {
  annotation_metrics: AnnotationMetrics;
  auto_grading_grade?: AutoGradingGrade;
};

/**
 * Response for `/api/dashboard/assignments/{assignment_id}/metrics` call.
 */
export type StudentsMetricsResponse = {
  students: StudentWithMetrics[];

  /**
   * Indicates the last time the students roster was updated.
   *
   * `null` indicates we don't have roster data and the list is based on
   * assignment launches.
   */
  last_updated: ISODateTime | null;
};

type AssignmentWithCourse = Assignment & {
  course: Course;
};

/**
 * - all_or_nothing: students need to meet a minimum value, making them get
 *                   either 0% or 100%
 * - scaled: students may get a proportional grade based on the amount of
 *           annotations. If requirement is 4, and they created 3, they'll
 *           get a 75%
 *
 * @todo `scaled` is now referenced as `proportional` in user-facing texts.
 *       We should consolidate it eventually.
 */
export type GradingType = 'all_or_nothing' | 'scaled';

/**
 * - cumulative: both annotations and replies will be counted together for
 *               the grade calculation
 * - separate: students will have different annotation and reply goals.
 */
export type ActivityCalculation = 'cumulative' | 'separate';

export type AutoGradingConfig = {
  grading_type: GradingType;
  activity_calculation: ActivityCalculation;

  /**
   * Required number of annotations if activityCalculation is 'separate' or
   * combined number of annotations and replies otherwise.
   */
  required_annotations: number;

  /** Required number of replies if activityCalculation is 'separate' */
  required_replies?: number;
};

/**
 * Represents an assignment group or section, which maps to an h group.
 */
export type AssignmentSegment = {
  h_authority_provided_id: string;
  name: string;
};

/** Assignments will have either sections, groups or neither, but never both */
type WithSegments =
  | { sections?: AssignmentSegment[] }
  | { groups?: AssignmentSegment[] };

/**
 * Response for `/api/dashboard/assignments/{assignment_id}` call.
 */
export type AssignmentDetails = AssignmentWithCourse &
  WithSegments & {
    /**
     * If defined, it indicates this assignment was configured with auto grading
     * enabled.
     */
    auto_grading_config?: AutoGradingConfig;
  };

export type AssignmentWithMetrics = AssignmentWithCourse & {
  annotation_metrics: AnnotationMetrics;
};

/**
 * Response for `/api/dashboard/courses/{course_id}/assignments/metrics` call.
 */
export type AssignmentsMetricsResponse = {
  assignments: AssignmentWithMetrics[];
};

export type Pagination = {
  next: string | null;
};

/**
 * Response for `/api/dashboard/courses` call.
 */
export type CoursesResponse = {
  courses: Course[];
  pagination: Pagination;
};

/**
 * Response for `/api/dashboard/assignments` call.
 */
export type AssignmentsResponse = {
  assignments: Assignment[];
  pagination: Pagination;
};

/**
 * Response for `/api/dashboard/students` call.
 */
export type StudentsResponse = {
  students: Student[];
  pagination: Pagination;
};

export type StudentGradingSyncStatus = 'in_progress' | 'finished' | 'failed';

export type StudentGradingSync = {
  h_userid: string;
  status: StudentGradingSyncStatus;
  grade: number;
};

export type GradingSyncStatus = 'scheduled' | StudentGradingSyncStatus;

/**
 * Response for `/api/dashboard/assignments/{assignment_id}/grading/sync`
 * That endpoint returns a 404 when an assignment has never been synced.
 */
export type GradingSync = {
  /**
   * Global sync status.
   * If at least one student grade is syncing, this will be `in_progress`.
   * If at least one student grade failed, this will be `failed`.
   * If all student grades finished successfully, this will be `finished`.
   */
  status: GradingSyncStatus;

  /**
   * The date and time when syncing grades finished.
   * It is null as long as status is `scheduled` or `in_progress`.
   */
  finish_date: ISODateTime | null;

  /**
   * Grading status for every individual student that was scheduled as part of
   * this sync.
   */
  grades: StudentGradingSync[];
};
