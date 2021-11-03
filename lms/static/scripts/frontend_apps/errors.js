/**
 * Error thrown when the user cancels file selection.
 */
export class PickerCanceledError extends Error {
  constructor() {
    super('Dialog was canceled');
  }
}

/**
 * @typedef {import('./config').ConfigErrorBase} ConfigErrorBase
 */

/**
 * Error returned when error data is provided in application configuration JSON
 * and application is in an error mode ('error-dialog' or 'oauth2-redirect-error')
 */
export class AppConfigError extends Error {
  /**
   * @param {ConfigErrorBase} data
   */
  constructor(data) {
    super();
    this.errorCode = data.errorCode;
    this.details = data.errorDetails;
  }
}

/**
 * Error returned when an API call fails.
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
    // If message is omitted, pass a default error message.
    const message = data.message || 'API call failed';
    super(message);

    /**
     * HTTP response status.
     */
    this.status = status;

    /**
     * Identifier for the specific error that happened.
     *
     * This can be used to show custom error dialogs for specific issues.
     */
    this.errorCode = data.error_code || null;

    /**
     * Server-provided error message.
     *
     * May be `null` if the server did not provide any details about what the
     * problem was.
     */
    this.errorMessage = data.message || null;

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
