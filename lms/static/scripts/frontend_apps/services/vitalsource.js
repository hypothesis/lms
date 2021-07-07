/**
 * @typedef {import('../api-types').Book} Book
 * @typedef {import('../api-types').Chapter} Chapter
 */

import { APIError } from '../utils/api';
import { bookList, chapterData } from '../utils/vitalsource-sample-data';

/** @param {number} ms */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

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
    // This field is not currently used. It will be in future to fetch book
    // and chapter info from the backend.
    this._authToken = authToken;
  }

  /**
   * Fetch a book by bookID ("vbid")
   *
   * This is currently a fake that waits for a fixed time before returning
   * hard-coded data.
   *
   * @param {string} bookID
   * @param {number} [fetchDelay] - Dummy delay to simulate slow third-party
   * @return {Promise<Book>}
   */
  async fetchBook(bookID, fetchDelay = 500) {
    await delay(fetchDelay);
    const book = bookList.find(b => b.id === bookID);
    if (!book) {
      throw new APIError(404, { message: 'Book not found' });
    }
    return book;
  }

  /**
   * Fetch a list of available ebooks to use in assignments.
   *
   * This is currently a fake that waits for a fixed time before returning
   * hard-coded data.
   *
   * @param {number} [fetchDelay] - Dummy delay to simulate slow third-party
   * @return {Promise<Book[]>}
   */
  async fetchBooks(fetchDelay = 500) {
    await delay(fetchDelay);
    return bookList;
  }

  /**
   * Fetch a list of chapters that can be used as the target location for an
   * ebook assignment.
   *
   * This is currently a fake that waits for a fixed time before returning
   * hard-coded data.
   *
   * @param {string} bookID - VitalSource book ID ("vbid")
   * @param {number} [fetchDelay] - Dummy delay to simulate slow third-party
   * @return {Promise<Chapter[]>}
   */
  async fetchChapters(bookID, fetchDelay = 500) {
    await delay(fetchDelay);
    if (!chapterData[bookID]) {
      throw new APIError(404, { message: 'Book not found' });
    }
    return chapterData[bookID];
  }
}
