import { useEffect, useRef, useState } from 'preact/hooks';

/**
 * @template T
 * @typedef FetchResult
 * @prop {T|null} data
 * @prop {Error|null} error
 * @prop {boolean} isLoading
 */

/**
 * Function that fetches the data.
 *
 * `signal` should be passed to the underlying data fetcher (eg. {@link fetch})
 * to support cancelation if possible.
 *
 * @template T
 * @typedef {(signal: AbortSignal) => Promise<T>} Fetcher
 */

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
 * @template [T=unknown]
 * @param {string|null} key - Key identifying the data to be fetched. The data
 *   will be re-fetched whenever this changes. If `null`, nothing will be fetched.
 * @param {Fetcher<T>} [fetcher] - Callback that fetches the data.
 * @return {FetchResult<T>}
 */
export function useFetch(key, fetcher) {
  const [result, setResult] = useState(
    /** @type {FetchResult<T>} */ ({
      data: null,
      error: null,
      isLoading: key !== null,
    })
  );

  const lastFetcher = useRef(fetcher);
  lastFetcher.current = fetcher;

  useEffect(() => {
    setResult({ data: null, error: null, isLoading: key !== null });

    if (!key) {
      return undefined;
    }

    if (!lastFetcher.current) {
      throw new Error('Fetch key provided but no fetcher set');
    }

    const controller = new AbortController();
    lastFetcher
      .current(controller.signal)
      .then(data => {
        if (!controller.signal.aborted) {
          setResult({ data, error: null, isLoading: false });
        }
      })
      .catch(error => {
        if (!controller.signal.aborted) {
          setResult({ data: null, error, isLoading: false });
        }
      });

    return () => {
      // Cancel in-flight request if query changes or component is unmounted.
      controller.abort();
    };
  }, [key]);

  return result;
}
