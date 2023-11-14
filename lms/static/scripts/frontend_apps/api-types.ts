/**
 * Types for objects exchanged between the LMS frontend and backend via
 * JSON HTTP requests.
 */
import type { APICallInfo } from './config';

/**
 * Object representing a file, folder or document stored by the LMS
 */
export type Document = {
  type?: 'File' | 'Folder' | 'Page';

  /** Identifier for the document within the LMS. */
  id: string;

  /** Name of the document to present in the document picker. */
  display_name: string;

  /** An ISO 8601 date string. */
  updated_at?: string;
};

/**
 * Object representing a file or folder in the LMS's file storage.
 */
export type File = Document & {
  // FIXME - This ought to be present on all file objects.
  type?: 'File' | 'Folder';

  /** APICallInfo for fetching a folder's content. Only present if `type` is 'Folder'. */
  contents?: APICallInfo;

  /** Only present if `type` is 'Folder'. A folder may have a parent folder. */
  parent_id?: string | null;

  /** Applies only when `type` is 'Folder'. A folder may contain children (files and folders). */
  children?: File[];
};

/**
 * Object representing Canvas pages or similar documents
 */
export type Page = Document & {
  type: 'Page';
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
