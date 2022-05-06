/** @typedef {import('../api-types').File} File */

/**
 * @typedef FileContent
 * @prop {'file'} type
 * @prop {File} file
 *
 * @typedef URLContent
 * @prop {'url'} type
 * @prop {string} url
 * @prop {string} [name] - (file)name of selected content (used for display
 *                         purposes only)
 *
 */

/**
 * Enumeration of the different types of content that may be used for an assignment.
 *
 * @typedef {FileContent|URLContent} Content
 */

// Make TypeScript treat this file as a module.
export const unused = {};
