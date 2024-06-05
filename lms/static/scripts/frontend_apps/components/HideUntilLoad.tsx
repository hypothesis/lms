import { Card, CardContent, Spinner } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { ComponentChildren } from 'preact';
import { useCallback, useMemo, useRef, useState } from 'preact/hooks';

import type { ErrorLike } from '../errors';
import { InitialLoadingContext } from '../utils/initial-loading-context';
import ErrorDisplay from './ErrorDisplay';

export type InitialLoadingProps = {
  children: ComponentChildren;

  /**
   * CSS classes to apply to the top-level element, regardless of it being the
   * loading indicator, error or children wrapper.
   */
  classes?: string | string[];

  /**
   * A component to render after initial load or when a fatal error has been
   * reported.
   * It is hidden during initial load.
   */
  footer?: ComponentChildren;
};

export default function HideUntilLoad({
  children,
  classes,
  footer,
}: InitialLoadingProps) {
  const [initialLoadInProgress, setInitialLoadInProgress] = useState(true);
  const [fatalError, setFatalError] = useState<ErrorLike>();
  const loadingInstances = useRef(new Set<string>());

  const startLoading = useCallback(
    (key: string) => loadingInstances.current.add(key),
    [],
  );
  const finishLoading = useCallback((key: string) => {
    loadingInstances.current.delete(key);
    // We consider loading is in progress as long as there are loading
    // instances.
    // Also, once we have transitioned from true to false once, we don't want
    // to go back to true ever again, considering the initial load has finished.
    setInitialLoadInProgress(prev => prev && loadingInstances.current.size > 0);
  }, []);
  const contextValue = useMemo(
    () => ({ startLoading, finishLoading, reportFatalError: setFatalError }),
    [finishLoading, startLoading],
  );
  const showLoadingIndicator = initialLoadInProgress && !fatalError;

  return (
    <InitialLoadingContext.Provider value={contextValue}>
      {showLoadingIndicator && (
        <div
          className={classnames(
            'flex items-center justify-center bg-white/50',
            classes,
          )}
          data-testid="initial-load-indicator"
        >
          <Spinner size="md" />
        </div>
      )}
      <div
        className={classnames(classes, { hidden: showLoadingIndicator })}
        data-testid="children-wrapper"
      >
        <div className="mx-auto max-w-6xl px-3 py-5">
          {!fatalError ? (
            children
          ) : (
            <Card>
              <CardContent>
                <ErrorDisplay error={fatalError} />
              </CardContent>
            </Card>
          )}
        </div>
      </div>
      {!showLoadingIndicator && footer}
    </InitialLoadingContext.Provider>
  );
}
