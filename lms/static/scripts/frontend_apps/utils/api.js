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
 * @param {string} options.path - The `/api/...` path of the endpoint to call
 * @param {string} options.authToken
 * @param {Object} [options.data] - JSON-serializable body of the request
 */
async function apiCall({ path, authToken, data }) {
  let body;
  const headers = {
    Authorization: authToken,
  };
  if (data !== undefined) {
    body = JSON.stringify(data);
    headers['Content-Type'] = 'application/json; charset=UTF-8';
  }

  const result = await fetch(path, {
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

async function listFiles(authToken, courseId) {
  return apiCall({
    authToken,
    path: `/api/canvas/courses/${courseId}/files`,
  });
}

// Separate export from declaration to work around
// https://github.com/robertknight/babel-plugin-mockable-imports/issues/9
export { apiCall, listFiles };
