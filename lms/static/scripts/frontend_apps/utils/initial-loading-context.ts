import { createContext } from 'preact';

import type { ErrorLike } from '../errors';

export type InitialLoadingContextState = {
  /**
   * Report the beginning of a loading that needs to be taken into
   * consideration for the initial load.
   *
   * @param id - The unique identifier for this loading instance
   */
  startLoading: (id: string) => void;

  /**
   * Report the end of a loading that needs to be taken into consideration
   * for the initial load.
   *
   * @param id - The same unique identifier that was first passed to
   *             startLoading. Unknown IDs will be ignored.
   */
  finishLoading: (id: string) => void;

  /** Report an error from which it is not possible to recover */
  reportFatalError: (error: ErrorLike) => void;
};

export const InitialLoadingContext =
  createContext<InitialLoadingContextState | null>(null);
