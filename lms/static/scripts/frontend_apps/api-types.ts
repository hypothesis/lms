/**
 * Types for objects exchanged between the LMS frontend and backend via
 * JSON HTTP requests.
 */
import type { APICallInfo } from './config';

/**
 * Object representing a file or folder resource in the LMS's file storage.
 */
export type File = {
  // FIXME - This ought to be present on all file objects.
  type?: 'File' | 'Folder';

  /** Identifier for the resource within the LMS's file storage. */
  id: string;

  /** Name of the resource to present in the file picker. */
  display_name: string;

  /** An ISO 8601 date string. */
  updated_at?: string;

  /** APICallInfo for fetching a folders's content. Only present if `type` is 'Folder'. */
  contents?: APICallInfo;

  /** Only present if `type` is 'Folder'. A folder may have a parent folder. */
  parent_id?: string | null;

  /** Applies only when `type` is 'Folder'. A folder may contain children (files and folders). */
  children?: File[];
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

/** Metadata for a chapter within an ebook. */
export type Chapter = {
  page: string;
  title: string;

  /** Document URL to use for this chapter when creating an assignment. */
  url: string;
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
