/**
 * Error thrown when the user cancels file selection.
 */
export class PickerCanceledError extends Error {
  constructor() {
    super('Dialog was canceled');
  }
}

/**
 * Error returned when an API call fails with a 4xx or 5xx response and
 * JSON body.
 */
export class APIError extends Error {
  /**
   * @param {number} status - HTTP status code
   * @param {object} data - Parsed JSON body from the API response
   *   @param {string} [data.message]
   *   @param {string} [data.error_code]
   *   @param {any} [data.details]
   */
  constructor(status, data) {
    super('API call failed');

    /**
     * HTTP response status.
     */
    this.status = status;

    /**
     * Identifier for the specific error that happened.
     *
     * This can be used to show custom error dialogs for specific issues.
     */
    this.errorCode = data.error_code;

    /**
     * Server-provided error message.
     *
     * May be empty if the server did not provide any details about what the
     * problem was.
     */
    this.errorMessage = data.message ?? '';

    /**
     * Server-provided details of the error.
     *
     * If provided, this will contain technical information about what the
     * problem was on the backend. This may be useful when handling eg.
     * support requests.
     */
    this.details = data.details;
  }
}
