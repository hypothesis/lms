import { SpinnerOverlay } from '@hypothesis/frontend-shared';
import type { ComponentChildren } from 'preact';
import { useEffect, useState } from 'preact/hooks';

import ErrorModal from './ErrorModal';

export type DataLoaderProps<Data> = {
  /**
   * Content to render if the required data is available.
   *
   * It is up to the parent component to store loaded data and pass it to
   * the content.
   */
  children: ComponentChildren;

  /**
   * Function that fetches data if {@link loaded} is false.
   * It provides an abort signal that gets aborted when the DataLoader is
   * unmounted or the `load` or `onLoad` props change.
   */
  load: (signal: AbortSignal) => Promise<Data>;

  /**
   * Callback to invoke with the results of {@link load}.
   *
   * The parent component should persist the data and re-render the
   * {@link DataLoader} and content with `loaded` set to `true`.
   */
  onLoad: (data: Data) => void;

  /** Boolean indicating whether the required data is available. */
  loaded: boolean;
};

/**
 * Component which renders its children if required data is loaded, or otherwise
 * initiates data loading and renders a loading indicator. If the content fails
 * to load, an error is displayed.
 *
 * This component doesn't store the fetched data. It is up to the parent to
 * handling persisting the data and passing it down to the content.
 */
export default function DataLoader<Data>({
  children,
  loaded,
  load,
  onLoad,
}: DataLoaderProps<Data>) {
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (loaded) {
      return () => {};
    }

    const controller = new AbortController();
    load(controller.signal)
      .then(onLoad)
      .catch(err => {
        setError(err);
      });

    return () => controller.abort();
  }, [loaded, load, onLoad]);

  if (error) {
    return (
      <ErrorModal
        description="There was a problem loading this content"
        error={error}
      />
    );
  } else if (!loaded) {
    return <SpinnerOverlay />;
  } else {
    return <>{children}</>;
  }
}
