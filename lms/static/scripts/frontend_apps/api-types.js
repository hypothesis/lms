/**
 * Types for objects exchanged between the LMS frontend and backend via
 * JSON HTTP requests.
 */

/**
 * @typedef {import("./config").APICallInfo} APICallInfo
 */

/**
 * Object representing a file or folder resource in the LMS's file storage.
 *
 * @typedef File
 * @prop {string} id - Identifier for the resource within the LMS's file storage
 * @prop {string} display_name - Name of the resource to present in the file picker
 * @prop {string} updated_at - An ISO 8601 date string
 * @prop {'File'|'Folder'} [type]
 * @prop {APICallInfo} [contents] - APICallInfo for fetching a folders's
 *   content. Only present if `type` is 'Folder'.
 * @prop {string|null} [parent_id] - Only present if `type` is 'Folder'. A
 *   folder may have a parent folder.
 */

/**
 * Object representing a set of groups that students can be divided into for
 * an assignment.
 *
 * @typedef GroupSet
 * @prop {string} id
 * @prop {string} name
 */

/**
 * Metadata for an ebook that is available to annotate.
 *
 * @typedef Book
 * @prop {string} id
 * @prop {string} title
 * @prop {string} cover_image - URL of a cover image for the book
 */

/**
 * Metadata for a chapter within an ebook.
 *
 * @typedef Chapter
 * @prop {string} cfi -
 *   An EPUB CFI indicating the location of the chapter within the book.
 *   See http://idpf.org/epub/linking/cfi/.
 * @prop {string} page
 * @prop {string} title
 */

// Make TS treat this file as a module.
export {};
