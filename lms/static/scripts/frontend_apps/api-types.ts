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

export type AnnotationMetrics = {
  last_activity: string | null;
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
  last_launched: string | null;
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
  created: string;
};

export type Student = {
  h_userid: string;
  lms_id: string;
  display_name: string | null;
};

export type StudentWithMetrics = Student & {
  annotation_metrics: AnnotationMetrics;
  auto_grading_grade?: number;
};

/**
 * Response for `/api/dashboard/assignments/{assignment_id}/metrics` call.
 */
export type StudentsMetricsResponse = {
  students: StudentWithMetrics[];
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
  required_annotations: number;
  required_replies?: number;
};

/**
 * Response for `/api/dashboard/assignments/{assignment_id}` call.
 */
export type AssignmentDetails = AssignmentWithCourse & {
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
