export type AppLaunchServerErrorCode =
  | 'reused_consumer_key'
  | 'vitalsource_student_pay_no_license';

export type OAuthServerErrorCode =
  | 'blackboard_missing_integration'
  | 'canvas_invalid_scope';

export type LTILaunchServerErrorCode =
  | 'blackboard_file_not_found_in_course'
  | 'blackboard_group_set_empty'
  | 'blackboard_group_set_not_found'
  | 'blackboard_student_not_in_group'
  | 'canvas_api_permission_error'
  | 'canvas_file_not_found_in_course'
  | 'canvas_group_set_empty'
  | 'canvas_group_set_not_found'
  | 'canvas_page_not_found_in_course'
  | 'canvas_student_not_in_group'
  | 'd2l_file_not_found_in_course_instructor'
  | 'd2l_file_not_found_in_course_student'
  | 'd2l_group_set_empty'
  | 'd2l_group_set_not_found'
  | 'd2l_student_not_in_group'
  | 'moodle_page_not_found_in_course'
  | 'moodle_file_not_found_in_course'
  | 'moodle_group_set_not_found'
  | 'moodle_group_set_empty'
  | 'moodle_student_not_in_group'
  | 'vitalsource_no_book_license'
  | 'vitalsource_user_not_found';

/**
 * An `Error` or error-like object. This allows components in the application
 * to work with plain-old JavaScript objects representing an error without
 * requiring `Error` instances.
 */
export type ErrorLike = {
  message?: string;

  /** Optional JSON-serializable details of the error. */
  details?: object | string;

  /** Provided by back-end to identify error state. */
  errorCode?: string;

  /** Explanatory message provided by backend that will be preferred over `message` if it is present. */
  serverMessage?: string;
};

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
   * HTTP response status.
   */
  public status: number;

  /**
   * Identifier for the specific error that happened.
   *
   * This can be used to show custom error dialogs for specific issues.
   */
  public errorCode: string | undefined;

  /**
   * Server-provided error message.
   *
   * May be empty if the server did not provide any details about what the
   * problem was.
   */
  public serverMessage: string;

  /**
   * Server-provided details of the error.
   *
   * If provided, this will contain technical information about what the
   * problem was on the backend. This may be useful when handling eg.
   * support requests.
   */
  public details: object | string | undefined;

  /**
   * @param status - HTTP status code
   * @param data - Parsed JSON body from the API response
   */
  constructor(
    status: number,
    data: { message?: string; error_code?: string; details?: object | string },
  ) {
    super('API call failed');

    this.status = status;
    this.errorCode = data.error_code;
    this.serverMessage = data.message ?? '';
    this.details = data.details;
  }
}

export function isAPIError(error: ErrorLike): error is APIError {
  return error instanceof APIError;
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
 */
export function isAuthorizationError(error: ErrorLike): boolean {
  return isAPIError(error) && !error.serverMessage && !error.errorCode;
}

/**
 * Does the error represent an API Error with a recognized
 * backend-provided `errorCode` related to a failed attempt to launch an
 * assignment?
 */
export function isLTILaunchServerError(error: ErrorLike): error is APIError {
  return (
    isAPIError(error) &&
    !!error.errorCode &&
    [
      'blackboard_file_not_found_in_course',
      'blackboard_group_set_empty',
      'blackboard_group_set_not_found',
      'blackboard_student_not_in_group',
      'd2l_file_not_found_in_course_instructor',
      'd2l_file_not_found_in_course_student',
      'd2l_group_set_not_found',
      'd2l_group_set_empty',
      'd2l_student_not_in_group',
      'canvas_api_permission_error',
      'canvas_file_not_found_in_course',
      'canvas_page_not_found_in_course',
      'canvas_group_set_not_found',
      'canvas_group_set_empty',
      'canvas_student_not_in_group',
      'vitalsource_user_not_found',
      'vitalsource_no_book_license',
      'moodle_page_not_found_in_course',
      'moodle_file_not_found_in_course',
      'moodle_group_set_not_found',
      'moodle_group_set_empty',
      'moodle_student_not_in_group',
    ].includes(error.errorCode)
  );
}

/**
 * Format a user-facing message based on this error and optional contextual
 * prefix, using the appropriate message information.
 */
export function formatErrorMessage(error: ErrorLike, prefix = ''): string {
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
 */
export function formatErrorDetails(error: ErrorLike): string {
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
