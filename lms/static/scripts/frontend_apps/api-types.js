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
 * Object representing a set of groups that students can be divided into for
 * an assignment.
 *
 * @typedef GroupSet
 * @prop {string} id
 * @prop {string} name
 */

// Make TS treat this file as a module.
export {};
