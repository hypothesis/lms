import { useStableCallback } from '@hypothesis/frontend-shared';
import { useCallback, useEffect, useRef, useState } from 'preact/hooks';

import type { Pagination } from '../api-types';
import { useConfig } from '../config';
import { APIError } from '../errors';
import { useFetch } from './fetch';
import type { FetchResult, Fetcher } from './fetch';
import type { QueryParams } from './url';
import { recordToQueryString } from './url';

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
  params?: QueryParams;

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

function isRetryableResponse(status: number, data: any): boolean {
  return status === 409 || (data && data.retryable);
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
  if (retryCount > 0) {
    headers['Retry-Count'] = `${retryCount}`;
  }

  if (data !== undefined) {
    body = JSON.stringify(data);
    headers['Content-Type'] = 'application/json; charset=UTF-8';
  }

  const query = recordToQueryString(params ?? {});
  const defaultMethod = data === undefined ? 'GET' : 'POST';
  const result = await fetch(path + query, {
    method: method ?? defaultMethod,
    body,
    headers,
    signal,
  });
  const resultJSON = await result.json();

  if (result.status >= 400 && result.status < 600) {
    if (
      isRetryableResponse(result.status, resultJSON) &&
      retryCount < maxRetries
    ) {
      await delay(retryDelay);
      return apiCall({
        ...options,
        retryCount: retryCount + 1,
      });
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
  params?: QueryParams,
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
  const paramStr = recordToQueryString(params ?? {});
  return useFetch(path ? `${path}${paramStr}` : null, fetcher);
}

export type PolledAPIFetchOptions<T> = {
  /** Path for API call */
  path: string | null;
  /** Query params for API call */
  params?: QueryParams;
  /** Determines if, based on the result, the API should be called again */
  shouldRefresh: (result: FetchResult<T>) => boolean;

  /**
   * Amount of ms after which a refresh should happen, if shouldRefresh()
   * returns true.
   * Defaults to 500ms.
   */
  refreshAfter?: number;

  /** Test seam */
  _setTimeout?: typeof setTimeout;
  /** Test seam */
  _clearTimeout?: typeof clearTimeout;
};

/**
 * Hook that fetches data using authenticated API requests.
 *
 * This is a variant of {@link useAPIFetch} that supports automatically
 * refreshing results at an interval until some condition is met.
 * This is useful for example when calling an API that reports the status of a
 * long-running operation.
 */
export function usePolledAPIFetch<T = unknown>({
  path,
  params,
  shouldRefresh: unstableShouldRefresh,
  refreshAfter = 500,
  /* istanbul ignore next - test seam */
  _setTimeout = setTimeout,
  /* istanbul ignore next - test seam */
  _clearTimeout = clearTimeout,
}: PolledAPIFetchOptions<T>): FetchResult<T> {
  const shouldRefresh = useStableCallback(unstableShouldRefresh);
  const result = useAPIFetch<T>(path, params);
  // Track loading state separately, to avoid flickering UIs due to
  // intermediate state changes between refreshes
  const [isLoading, setIsLoading] = useState(result.isLoading);
  // Track data from previous fetch, so that we can expose it and differentiate
  // the first fetch from subsequent refreshes.
  const [prevData, setPrevData] = useState(result.data);

  const timeout = useRef<ReturnType<typeof _setTimeout> | null>(null);
  const resetTimeout = useCallback(() => {
    if (timeout.current) {
      _clearTimeout(timeout.current);
    }
    timeout.current = null;
  }, [_clearTimeout]);

  useEffect(() => {
    if (result.data) {
      setPrevData(result.data);
    }

    // When the actual request is loading, transition to loading, in case
    // a new request was triggered by a path/fetch key change
    if (result.isLoading) {
      setIsLoading(true);
      return () => {};
    }

    // Transition to not-loading only once we no longer have to refresh
    if (!shouldRefresh(result)) {
      setIsLoading(false);
      // Reset prev data once we finish refreshing, so that we don't
      // accidentally leak data from a different request on subsequent ones
      setPrevData(null);
      return () => {};
    }

    // Once we finish loading, schedule a retry if the request should be
    // refreshed
    timeout.current = _setTimeout(() => {
      result.retry();
      timeout.current = null;
    }, refreshAfter);

    return resetTimeout;
  }, [_setTimeout, refreshAfter, resetTimeout, result, shouldRefresh]);

  return {
    ...result,
    // If the fetch result data is available, return it. Otherwise, fall back
    // to the data loaded in previous fetch
    data: result.data ?? prevData,
    isLoading,
  };
}

export type PaginatedFetchResult<T> = Omit<FetchResult<T>, 'mutate'> & {
  /** Determines if currently loading the first page */
  isLoadingFirstPage: boolean;
  loadNextPage: () => void;

  /**
   * The size of every page (maximum number of results returned per page).
   * If the API indicates there is only one page, this will be undefined. You
   * can trust `data.length` as the total number of items in that case.
   */
  pageSize?: number;

  /**
   * Whether there are still more pages to load or not.
   * The value is `undefined` during the first page load, when it's still not
   * possible to know.
   */
  hasMorePages?: boolean;
};

/**
 * Hook that fetches paginated data using authenticated API requests.
 * It expects the result to include pagination info in a `pagination` prop.
 * Resulting object will allow further pages to be loaded, while `error` and
 * `retry` will apply only to the last attempted page load.
 *
 * @param prop - Property of responses containing a page of results
 * @param path - Path for API call, or null if there is nothing to fetch
 * @param [params] - Query params for API call
 */
export function usePaginatedAPIFetch<
  Prop extends string,
  ListType extends any[],
  FetchType extends { [P in Prop]: ListType } & { pagination: Pagination },
>(
  prop: Prop,
  path: string | null,
  params?: QueryParams,
): PaginatedFetchResult<ListType> {
  const [nextPageURL, setNextPageURL] = useState<string>();
  const [currentList, setCurrentList] = useState<ListType>();
  const [pageSize, setPageSize] = useState<number>();
  const [hasMorePages, setHasMorePages] = useState<boolean>();

  const fetchResult = useAPIFetch<FetchType>(
    nextPageURL ?? path,
    !nextPageURL ? params : undefined,
  );

  const loadNextPage = useCallback(() => {
    if (!fetchResult.isLoading && fetchResult.data?.pagination.next) {
      setNextPageURL(fetchResult.data.pagination.next);
    }
  }, [fetchResult.data?.pagination.next, fetchResult.isLoading]);

  useEffect(() => {
    if (!fetchResult.data) {
      return;
    }

    const data = fetchResult.data;
    const hasMorePages = !!data.pagination.next;

    // Every time data is loaded, append the result to the list
    setCurrentList(prev => [...(prev ?? []), ...data[prop]] as ListType);
    setHasMorePages(hasMorePages);

    // Set pageSize if the API indicated there are more pages.
    // Once page size has been set, we keep the value, ignoring next page loads
    if (hasMorePages) {
      setPageSize(prev => prev ?? data[prop].length);
    }
  }, [prop, fetchResult.data]);

  // Every time params change, discard previous pages and start from scratch
  const prevParamsRef = useRef<typeof params>(params);
  useEffect(() => {
    const prevParams = JSON.stringify(prevParamsRef.current);
    const newParams = JSON.stringify(params);

    if (prevParams !== newParams) {
      setCurrentList(undefined);
      setNextPageURL(undefined);
    }

    prevParamsRef.current = params;
  }, [params]);

  return {
    isLoading: fetchResult.isLoading,
    isLoadingFirstPage: fetchResult.isLoading && currentList === undefined,
    data: currentList ?? null,
    error: fetchResult.error,
    retry: fetchResult.retry,
    loadNextPage,
    pageSize,
    hasMorePages,
  };
}
