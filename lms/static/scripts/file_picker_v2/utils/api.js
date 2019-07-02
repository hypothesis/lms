/**
 * Error returned when an API call fails with a 4xx or 5xx response and
 * JSON body.
 */
export class ApiError extends Error {
  constructor(status, data) {
    const message = data.error_message || data.message || 'API call failed';
    super(message);

    /**
     * HTTP response status.
     *
     * @type {number}
     */
    this.status = status;

    /**
     * Server-provided error message.
     *
     * May be `null` if the server did not provide any details about what the
     * problem was.
     *
     * @type {string|null}
     */
    this.errorMessage = data.error_message || null;

    /**
     *
     * @type {Object|undefined}
     */
    this.details = data.details;
  }
}

/**
 * Make an API call to the LMS app backend.
 *
 * @param options
 * @param {string} options.path
 * @param {string} options.authToken
 */
async function apiCall({ path, authToken }) {
  const result = await fetch(path, {
    headers: {
      Authorization: authToken,
    },
  });
  const data = await result.json();

  if (result.status >= 400 && result.status < 600) {
    throw new ApiError(result.status, data);
  }

  return data;
}

async function listFiles(authToken, courseId) {
  return apiCall({
    authToken,
    path: `/api/canvas/courses/${courseId}/files`,
  });
}

// Separate export from declaration to work around
// https://github.com/robertknight/babel-plugin-mockable-imports/issues/9
export { listFiles };
