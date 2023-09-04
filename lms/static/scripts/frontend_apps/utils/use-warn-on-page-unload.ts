import { useEffect } from 'preact/hooks';

const noop = () => {};

/**
 * Registers an event listener to window's 'beforeunload' if `hasUnsavedData` is true.
 * It also unregisters the event if `hasUnsavedData` is false or the component is unmounted.
 *
 * This event listener makes the browser warn the user about potential unsaved changes,
 * and gives the user the opportunity to cancel the page unload if desired.
 *
 * @link https://developer.mozilla.org/en-US/docs/Web/API/Window/beforeunload_event
 */
export function useWarnOnPageUnload(hasUnsavedData: boolean, window_ = window) {
  useEffect(() => {
    if (!hasUnsavedData) {
      return noop;
    }

    const listener = (e: BeforeUnloadEvent) => {
      e.preventDefault();
      e.returnValue = '';
    };

    window_.addEventListener('beforeunload', listener);

    return () => window_.removeEventListener('beforeunload', listener);
  }, [hasUnsavedData, window_]);
}
