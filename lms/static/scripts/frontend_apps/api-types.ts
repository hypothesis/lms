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

export type BaseDashboardStats = {
  last_activity: string | null;
  annotations: number;
  replies: number;
};

/**
 * Response for `/dashboard/api/assignment/{assignment_id}` call.
 */
export type Assignment = {
  id: number;
  title: string;
};

/**
 * Response for `/dashboard/api/assignment/{assignment_id}/stats` call.
 */
export type StudentStats = BaseDashboardStats & {
  display_name: string;
};

export type StudentsStats = StudentStats[];

/**
 * Response for `/dashboard/api/course/{course_id}` call.
 */
export type Course = {
  id: number;
  title: string;
};

/**
 * Response for `/dashboard/api/course/{course_id}/stats` call.
 */
export type AssignmentStats = {
  id: number;
  title: string;
  course: Course;
  stats: BaseDashboardStats;
};

export type AssignmentsStats = AssignmentStats[];
