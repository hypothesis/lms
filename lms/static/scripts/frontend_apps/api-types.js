/**
 * Types for objects exchanged between the LMS frontend and backend via
 * JSON HTTP requests.
 */

/**
 * Object representing a file in the LMS's file storage.
 *
 * @typedef File
 * @prop {string} id - Identifier for the file within the LMS's file storage
 * @prop {string} display_name - Name of the file to present in the file picker
 * @prop {string} updated_at - An ISO 8601 date string
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
