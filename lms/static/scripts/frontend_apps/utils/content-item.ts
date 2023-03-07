import type { File } from '../api-types';

export type FileContent = {
  type: 'file';
  file: File;
};

export type URLContent = {
  type: 'url';
  url: string;

  /** Filename of selected content. Used for display purposes only. */
  name?: string;
};

/**
 * Enumeration of the different types of content that may be used for an assignment.
 */
export type Content = FileContent | URLContent;
