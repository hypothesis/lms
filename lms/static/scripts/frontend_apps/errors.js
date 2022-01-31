/**
 * @typedef {'reused_consumer_key'} AppLaunchServerErrorCode
 *
 * @typedef {'blackboard_missing_integration'|'canvas_invalid_scope'} OAuthServerErrorCode
 *
 * @typedef {'blackboard_file_not_found_in_course'|
 *           'blackboard_group_set_empty' |
 *           'blackboard_group_set_not_found' |
 *           'blackboard_student_not_in_group' |
 *           'canvas_api_permission_error'|
 *           'canvas_file_not_found_in_course'|
 *           'canvas_group_set_not_found'|
 *           'canvas_group_set_empty'|
 *           'canvas_student_not_in_group'} LTILaunchServerErrorCode
 */

/**
 * An `Error` or error-like object. This allows components in the application
 * to work with plain-old JavaScript objects representing an error without
 * requiring `Error` instances.
 *
 * @typedef ErrorLike
 * @prop {string} [message]
 * @prop {object|string} [details] - Optional JSON-serializable details of the error
 * @prop {string} [errorCode] - Provided by back-end to identify error state
 * @prop {string} [serverMessage] - Explanatory message provided by backend that
 *   will be preferred over `message` if it is present.
 */

/**
 * Error raised when a course's list of groups is empty (as returned from the
 * API).
 */
export class GroupListEmptyError extends Error {
  constructor() {
    super('This course has no groups');
  }
}

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
 * Should the error be treated as an authorization error?
 *
 * This is a special case. We're handling an APIError resulting from an API
 * request, but there are no further details in the response body to guide us.
 * This implicitly means that we're facing an authorization-related issue.
 *
 * Put another way, if an APIError has neither an errorCode nor a serverMessage,
 * it is considered an "authorization error".
 *
 * @param {ErrorLike} error
 * @returns {boolean}
 */
export function isAuthorizationError(error) {
  return error instanceof APIError && !error.serverMessage && !error.errorCode;
}

/**
 * Does the error represent an API Error with a recognized
 * backend-provided `errorCode` related to a failed attempt to launch an
 * assignment?
 *
 * @param {ErrorLike} error
 * @returns {error is APIError}
 */
export function isLTILaunchServerError(error) {
  return (
    error instanceof APIError &&
    !!error.errorCode &&
    [
      'blackboard_file_not_found_in_course',
      'blackboard_group_set_empty',
      'blackboard_group_set_not_found',
      'blackboard_student_not_in_group',
      'canvas_api_permission_error',
      'canvas_file_not_found_in_course',
      'canvas_group_set_not_found',
      'canvas_group_set_empty',
      'canvas_student_not_in_group',
    ].includes(error.errorCode)
  );
}

/**
 * Format a user-facing message based on this error and optional contextual
 * prefix, using the appropriate message information.
 *
 * @param {ErrorLike} error
 * @param {string} [prefix]
 * @returns {string}
 */
export function formatErrorMessage(error, prefix = '') {
  // If any message is provided by the backend as `error.serverMessage`,
  // prefer this for display to users even if it is empty.
  const message = error.serverMessage ?? error.message ?? '';

  // Create an error status message from the combination of `description` and
  // `message`. As neither of these are guaranteed to be present, the
  // resulting string may be empty.
  return `${prefix}${prefix && message ? ': ' : ''}${message}`;
}

/**
 * Return a string representing error details. If `error.details` is an
 * object, attempt to JSON-stringify it. If details is already a string, return
 * it as-is. Return the empty string otherwise.
 *
 * @param {ErrorLike} error
 * @returns {string}
 */
export function formatErrorDetails(error) {
  let details = '';
  if (error.details && typeof error.details === 'object') {
    try {
      details = JSON.stringify(error.details, null, 2 /* indent */);
    } catch (e) {
      // ignore
    }
  } else if (error.details) {
    details = error.details;
  }
  return details;
}
