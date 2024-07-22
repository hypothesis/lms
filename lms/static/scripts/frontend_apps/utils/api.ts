import { useConfig } from '../config';
import { APIError } from '../errors';
import { useFetch } from './fetch';
import type { FetchResult, Fetcher } from './fetch';
import { recordToSearchParams } from './url';

/**
 * Parameters for an API call that will refresh an expired access token.
 */
export type RefreshCall = { method: string; path: string };

/**
 * Error response when a call fails due to expiry of an access token for an
 * external API.
 */
export type RefreshError = { refresh: RefreshCall };

/**
 * Check if an API error response indicates that a token refresh is needed.
 *
 * @param data - Parsed body of an API error response
 */
function isRefreshError(data: any): data is RefreshError {
  return data && data.refresh && typeof data.refresh === 'object';
}

/**
 * Map of request path to result promise for access token refresh requests that are
 * in flight.
 *
 * This is used to avoid triggering concurrent refresh requests for the same
 * external API.
 */
const activeRefreshCalls = new Map<string, Promise<void>>();

export type APICallOptions = {
  /** Session authorization token. */
  authToken: string;

  /**
   * The `/api/...` path of the endpoint to call.
   *
   * If the path contains parameters, use {@link urlPath} to generate this.
   */
  path: string;

  /** Query parameters. */
  params?: Record<string, string | string[]>;

  /** JSON-serializable body of request. */
  data?: object;

  /** HTTP method to use. Defaults to POST if `data` is defined or GET otherwise. */
  method?: string;

  /**
   * Whether to attempt to refresh the token if it fails due to an expired
   * access token for an external API.
   */
  allowRefresh?: boolean;

  /**
   * Maximum number of times this request can be retried automatically due to
   * eg. HTTP 409 (Conflict) responses.
   */
  maxRetries?: number;

  /** Internal. Counts the number of times this request has been retried. */
  retryCount?: number;

  /** Internal. Amount of time to wait between retries. */
  retryDelay?: number;

  /** Signal that can be used to cancel the request. */
  signal?: AbortSignal;
};

function delay(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Make an API call to the LMS app backend.
 */
export async function apiCall<Result = unknown>(
  options: APICallOptions,
): Promise<Result> {
  const {
    authToken,
    path,

    // Optional fields.
    allowRefresh = true,
    data,
    maxRetries = 10,
    method,
    params,
    retryCount = 0,
    retryDelay = 1000,
    signal,
  } = options;

  let body;

  const headers: Record<string, string> = {
    Authorization: authToken,
  };

  if (data !== undefined) {
    body = JSON.stringify(data);
    headers['Content-Type'] = 'application/json; charset=UTF-8';
  }

  const queryString = recordToSearchParams(params ?? {}).toString();
  const query = queryString.length > 0 ? `?${queryString}` : '';

  const defaultMethod = data === undefined ? 'GET' : 'POST';
  const result = await fetch(path + query, {
    method: method ?? defaultMethod,
    body,
    headers,
    signal,
  });
  const resultJSON = await result.json();

  if (result.status >= 400 && result.status < 600) {
    if (result.status === 409 && retryCount < maxRetries) {
      await delay(retryDelay);
      return apiCall({ ...options, retryCount: retryCount + 1 });
    }

    // Refresh expired access tokens for external APIs, if required. Only one
    // such request should be issued by the frontend for a given API at a time.
    if (allowRefresh && result.status === 400 && isRefreshError(resultJSON)) {
      const { method, path } = resultJSON.refresh;

      // Refresh the access token for the external API.
      if (activeRefreshCalls.has(path)) {
        await activeRefreshCalls.get(path);
      } else {
        const refreshDone = apiCall<void>({
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
 * Template tag function that formats a URL path, ensuring interpolated strings
 * are percent-encoded.
 *
 * @example
 *   // Assume `widgetId` is "foo/bar"
 *   urlPath`/api/widgets/${widgetId}` => `/api/widgets/foo%2Fbar`
 */
export function urlPath(strings: TemplateStringsArray, ...params: string[]) {
  let result = '';
  for (const [i, param] of params.entries()) {
    result += strings[i];
    result += encodeURIComponent(param);
  }
  return result + strings[strings.length - 1];
}

/**
 * Hook that fetches data using authenticated API requests.
 *
 * @param path - Path for API call, or null if there is nothing to fetch
 * @param [params] - Query params for API call
 */
export function useAPIFetch<T = unknown>(
  path: string | null,
  params?: Record<string, string | string[]>,
): FetchResult<T> {
  const {
    api: { authToken },
  } = useConfig(['api']);

  const fetcher: Fetcher<T> | undefined = path
    ? signal =>
        apiCall({
          authToken,
          path,
          params,
          signal,
        })
    : undefined;

  // We generate a URL-like key from the path and params, but we could generate
  // something simpler, as long as it encodes the same information. The auth
  // token is not included in the key, as we assume currently that it does not
  // change the result.
  const queryString = recordToSearchParams(params ?? {}).toString();
  const paramStr = queryString.length > 0 ? `?${queryString}` : '';
  return useFetch(path ? `${path}${paramStr}` : null, fetcher);
}
