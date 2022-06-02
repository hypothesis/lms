import { APIError } from '../errors';

/**
 * Error response when a call fails due to expiry of an access token for an
 * external API.
 *
 * @typedef RefreshError
 * @prop {RefreshCall} refresh
 */

/**
 * Parameters for an API call that will refresh an expired access token.
 *
 * @typedef RefreshCall
 * @prop {string} method
 * @prop {string} path
 */

/**
 * Check if an API error response indicates that a token refresh is needed.
 *
 * @param {any} data - Parsed body of an API error response
 * @return {data is RefreshError}
 */
function isRefreshError(data) {
  return data && data.refresh && typeof data.refresh === 'object';
}

/**
 * Map of request path to result promise for access token refresh requests that are
 * in flight.
 *
 * This is used to avoid triggering concurrent refresh requests for the same
 * external API.
 *
 * @type {Map<string, Promise<void>>}
 */
const activeRefreshCalls = new Map();

/**
 * Make an API call to the LMS app backend.
 *
 * @param {object} options
 *   @param {string} options.authToken - Session authorization token
 *   @param {string} options.path - The `/api/...` path of the endpoint to call.
 *     If this path contains parameters, use {@link urlPath} to generate this.
 *   @param {boolean} [options.allowRefresh] - If the request fails due to
 *     an expired access token for an external API, this flag specifies whether
 *     to attempt to refresh the token.
 *   @param {object} [options.data] - JSON-serializable body of the request
 *   @param {string} [options.method] - Custom HTTP method for call. Defaults
 *     to GET, or POST if `data` is set.
 *   @param {AbortSignal} [options.signal]
 *   @param {Record<string, string>} [options.params] - Query parameters
 * @return {Promise<any>} - Parsed JSON response. TODO: Convert this to `Promise<unknown>`
 */
export async function apiCall(options) {
  const {
    authToken,
    path,

    // Optional fields.
    allowRefresh = true,
    data,
    method,
    params,
    signal,
  } = options;

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

  const defaultMethod = data === undefined ? 'GET' : 'POST';
  const result = await fetch(path + query, {
    method: method ?? defaultMethod,
    body,
    headers,
    signal,
  });
  const resultJSON = await result.json();

  if (result.status >= 400 && result.status < 600) {
    // Refresh expired access tokens for external APIs, if required. Only one
    // such request should be issued by the frontend for a given API at a time.
    if (allowRefresh && result.status === 400 && isRefreshError(resultJSON)) {
      const { method, path } = resultJSON.refresh;

      // Refresh the access token for the external API.
      if (activeRefreshCalls.has(path)) {
        await activeRefreshCalls.get(path);
      } else {
        const refreshDone = apiCall({
          authToken,
          method,
          path,
          allowRefresh: false,
          signal,
        });
        activeRefreshCalls.set(path, refreshDone);
        try {
          await refreshDone;
        } finally {
          activeRefreshCalls.delete(path);
        }
      }

      // Retry the original API call.
      return apiCall({ ...options, allowRefresh: false });
    }

    throw new APIError(result.status, resultJSON);
  }

  return resultJSON;
}

/**
 * Template tag that formats a URL path, ensuring interpolated strings are
 * percent-encoded.
 *
 * @example
 *   // Assume `widgetId` is "foo/bar"
 *   urlPath`/api/widgets/${widgetId}` => `/api/widgets/foo%2Fbar`
 *
 * @param {TemplateStringsArray} strings
 * @param {string[]} params
 */
export function urlPath(strings, ...params) {
  let result = '';
  for (const [i, param] of params.entries()) {
    result += strings[i];
    result += encodeURIComponent(param);
  }
  return result + strings[strings.length - 1];
}
