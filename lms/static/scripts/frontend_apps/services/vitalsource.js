/**
 * @typedef {import('../api-types').Book} Book
 * @typedef {import('../api-types').Chapter} Chapter
 */

import { apiCall } from '../utils/api';

/**
 * Service for fetching information about available VitalSoure books and the
 * list of chapters in a book.
 */
export class VitalSourceService {
  /**
   * @param {object} options
   *   @param {string} options.authToken
   */
  constructor({ authToken }) {
    this._authToken = authToken;
  }

  /**
   * Fetch metadata about a VitalSource book.
   *
   * @param {string} bookID - VitalSource book ID (aka "vbid")
   * @return {Promise<Book>}
   */
  async fetchBook(bookID) {
    // Path parameter encoding is currently handled by the `apiCall` caller,
    // but this should be done by `apiCall` in future.
    return apiCall({
      path: `/api/vitalsource/books/${encodeURIComponent(bookID)}`,
      authToken: this._authToken,
    });
  }

  /**
   * Fetch a list of chapters that can be used as the target location for an
   * ebook assignment.
   *
   * @param {string} bookID - VitalSource book ID ("vbid")
   * @return {Promise<Chapter[]>}
   */
  async fetchChapters(bookID) {
    return apiCall({
      path: `/api/vitalsource/books/${encodeURIComponent(bookID)}/toc`,
      authToken: this._authToken,
    });
  }
}
