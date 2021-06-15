/**
 * @typedef {import('../api-types').Book} Book
 * @typedef {import('../api-types').Chapter} Chapter
 * @typedef {import('../api-types').File} File
 */

import { bookList, chapterData } from './vitalsource-sample-data';

/**
 * Error returned when an API call fails with a 4xx or 5xx response and
 * JSON body.
 */
export class ApiError extends Error {
  /**
   * @param {number} status - HTTP status code
   * @param {any} data - Parsed JSON body from the API response
   */
  constructor(status, data) {
    // If message is omitted, pass a default error message.
    const message = data.message || 'API call failed';
    super(message);

    /**
     * HTTP response status.
     *
     * @type {number}
     */
    this.status = status;

    /**
     * Identifier for the specific error that happened.
     *
     * This can be used to show custom error dialogs for specific issues.
     *
     * @type {string|null}
     */
    this.errorCode = data.error_code || null;

    /**
     * Server-provided error message.
     *
     * May be `null` if the server did not provide any details about what the
     * problem was.
     *
     * @type {string|null}
     */
    this.errorMessage = data.message || null;

    /**
     * Server-provided details of the error.
     *
     * If provided, this will contain technical information about what the
     * problem was on the backend. This may be useful when handling eg.
     * support requests.
     *
     * @type {any}
     */
    this.details = data.details;
  }
}

/**
 * Make an API call to the LMS app backend.
 *
 * @param {Object} options
 *   @param {string} options.path - The `/api/...` path of the endpoint to call
 *   @param {string} options.authToken
 *   @param {Record<string, string>} [options.params] - Query parameters
 *   @param {Object} [options.data] - JSON-serializable body of the request
 */
export async function apiCall({ path, authToken, data, params }) {
  let body;

  /** @type {Record<string,string>} */
  const headers = {
    Authorization: authToken,
  };

  if (data !== undefined) {
    body = JSON.stringify(data);
    headers['Content-Type'] = 'application/json; charset=UTF-8';
  }

  let query = '';
  if (params) {
    const urlParams = new URLSearchParams();
    Object.entries(params).forEach(([name, value]) =>
      urlParams.append(name, value)
    );
    query = `?${urlParams}`;
  }

  const result = await fetch(path + query, {
    method: data === undefined ? 'GET' : 'POST',
    body,
    headers,
  });
  const resultJson = await result.json();

  if (result.status >= 400 && result.status < 600) {
    throw new ApiError(result.status, resultJson);
  }

  return resultJson;
}

/** @param {number} ms */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Fetch a list of available ebooks to use in assignments.
 *
 * This is currently a fake that waits for a fixed time before returning
 * hard-coded data.
 *
 * @param {string} authToken
 * @param {number} [fetchDelay] - Dummy delay to simulate slow third-party
 * @return {Promise<Book[]>}
 */
export async function fetchBooks(authToken, fetchDelay = 500) {
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
 * @param {string} authToken
 * @param {string} bookId
 * @param {number} [fetchDelay] - Dummy delay to simulate slow third-party
 * @return {Promise<Chapter[]>}
 */
export async function fetchChapters(authToken, bookId, fetchDelay = 500) {
  await delay(fetchDelay);
  if (!chapterData[bookId]) {
    throw new ApiError(404, { message: 'Book not found' });
  }
  return chapterData[bookId];
}
