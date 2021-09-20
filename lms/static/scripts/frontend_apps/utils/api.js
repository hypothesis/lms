/**
 * Error returned when an API call fails with a 4xx or 5xx response and
 * JSON body.
 */
export class APIError extends Error {
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
 * @param {object} options
 *   @param {string} options.path - The `/api/...` path of the endpoint to call
 *   @param {string} options.authToken
 *   @param {object} [options.data] - JSON-serializable body of the request
 *   @param {Record<string, string>} [options.params] - Query parameters
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
    query = '?' + urlParams.toString();
  }

  const result = await fetch(path + query, {
    method: data === undefined ? 'GET' : 'POST',
    body,
    headers,
  });
  const resultJson = await result.json();

  if (result.status >= 400 && result.status < 600) {
    throw new APIError(result.status, resultJson);
  }

  return resultJson;
}
