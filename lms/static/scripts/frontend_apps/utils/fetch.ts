import { useEffect, useRef, useState } from 'preact/hooks';

export type FetchResult<T> = {
  data: T | null;
  error: Error | null;
  isLoading: boolean;

  /**
   * Set the fetched result to `data`. This is useful to update the result of
   * a {@link useFetch} callback following an API call to update it on the
   * backend.
   *
   * `newValue` should be the same as the value that would be returned by a
   * re-fetch using `retry`. This method does not currently verify this.
   */
  mutate: (newValue: T) => void;

  /**
   * Callback which retries the fetch. This does nothing if there is nothing
   * to fetch or the fetch has not yet finished.
   */
  retry: () => void;
};

/**
 * Function that fetches the data.
 *
 * `signal` should be passed to the underlying data fetcher (eg. {@link fetch})
 * to support cancelation if possible.
 */
export type Fetcher<T> = (signal: AbortSignal) => Promise<T>;

/**
 * Hook that fetches data from the backend API or some other async data source.
 *
 * The API is intentionally very similar to SWR (https://swr.vercel.app), so
 * we can easily migrate if we need its additional functionality in future.
 *
 * This hook handles:
 *
 *  - Tracking the state of the fetch (idle, fetching, fetched, error)
 *  - Initiating a fetch when the data to be fetched changes
 *  - Canceling in-flight requests when the query changes or the component is
 *    unmounted
 *
 * @param key - Key identifying the data to be fetched. The data
 *   will be re-fetched whenever this changes. If `null`, nothing will be fetched.
 * @param [fetcher] - Callback that fetches the data.
 */
export function useFetch<T = unknown>(
  key: string | null,
  fetcher?: Fetcher<T>,
): FetchResult<T> {
  const [result, setResult] = useState<FetchResult<T>>({
    data: null,
    error: null,
    isLoading: key !== null,
    mutate: /* istanbul ignore next */ () => null,
    retry: /* istanbul ignore next */ () => null,
  });

  const lastFetcher = useRef(fetcher);
  lastFetcher.current = fetcher;

  useEffect(() => {
    const controller = new AbortController();
    const mutate = (newValue: T) => {
      // Prevent in-flight fetch from overwriting this value.
      controller.abort();
      setResult(r => ({ ...r, error: null, isLoading: false, data: newValue }));
    };
    const resetResult = () =>
      setResult({
        data: null,
        error: null,
        isLoading: key !== null,
        mutate,
        retry: () => null,
      });
    resetResult();

    if (!key) {
      return undefined;
    }

    if (!lastFetcher.current) {
      throw new Error('Fetch key provided but no fetcher set');
    }

    const fetcher = lastFetcher.current;
    const doFetch = () => {
      resetResult();
      fetcher(controller.signal)
        .then(data => {
          if (!controller.signal.aborted) {
            setResult({
              data,
              error: null,
              isLoading: false,
              mutate,
              retry: doFetch,
            });
          }
        })
        .catch(error => {
          if (!controller.signal.aborted) {
            setResult({
              data: null,
              error,
              isLoading: false,
              mutate,
              retry: doFetch,
            });
          }
        });
    };
    doFetch();

    return () => {
      // Cancel in-flight request if query changes or component is unmounted.
      controller.abort();
    };
  }, [key]);

  return result;
}
