import { APIError } from '../errors';

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
