/**
 * @typedef {'reused_consumer_key'} AppLaunchServerErrorCode
 *
 * @typedef {'blackboard_missing_integration'|'canvas_invalid_scope'} OAuthServerErrorCode
 *
 * @typedef {'blackboard_file_not_found_in_course'|
 *           'canvas_api_permission_error'|
 *           'canvas_file_not_found_in_course'|
 *           'canvas_group_set_not_found'|
 *           'canvas_group_set_empty'|
 *           'canvas_student_not_in_group'} LTILaunchServerErrorCode
 */

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
    this.serverMessage = data.message ?? '';

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

/**
 * Should the error object be treated as an authorization error?
 *
 * This is a special case. We're handling an APIError resulting from an API
 * request, but there are no further details in the response body to guide us.
 * This implicitly means that we're facing an authorization-related issue.
 *
 * Put another way, if an APIError has neither an errorCode nor a serverMessage,
 * it is considered an "authorization error".
 *
 * @param {Error} error
 * @returns {boolean}
 */
export function isAuthorizationError(error) {
  return error instanceof APIError && !error.serverMessage && !error.errorCode;
}

/**
 * Does the current error object represent an API Error with a recognized
 * backend-provided `errorCode` related to a failed attempt to launch an
 * assignment?
 *
 * @param {Error} error
 * @returns {error is APIError}
 */
export function isLTILaunchServerError(error) {
  return (
    error instanceof APIError &&
    !!error.errorCode &&
    [
      'blackboard_file_not_found_in_course',
      'canvas_api_permission_error',
      'canvas_file_not_found_in_course',
      'canvas_group_set_not_found',
      'canvas_group_set_empty',
      'canvas_student_not_in_group',
    ].includes(error.errorCode)
  );
}
