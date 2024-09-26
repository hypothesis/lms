import { Button, MultiSelect, RefreshIcon } from '@hypothesis/frontend-shared';
import type { ComponentChildren } from 'preact';
import type { MutableRef } from 'preact/hooks';
import { useRef } from 'preact/hooks';

import type { PaginatedFetchResult } from '../../utils/api';

type FiltersEntity = 'courses' | 'assignments' | 'students';

/**
 * Placeholder to indicate a loading is in progress in one of the dropdowns
 */
function LoadingOption({ entity }: { entity: FiltersEntity }) {
  return (
    <div className="py-2 px-4 mb-1 text-grey-4 italic">
      Loading more {entity}...
    </div>
  );
}

type LoadingErrorProps = {
  entity: FiltersEntity;
  retry: () => void;
};

/**
 * Indicates an error occurred while loading filters, and presents a button to
 * retry.
 */
function LoadingError({ entity, retry }: LoadingErrorProps) {
  return (
    <div
      className="flex gap-2 items-center py-2 pl-4 pr-2.5 mb-1"
      // Make this element "focusable" so that clicking on it does not cause
      // the listbox containing it to be closed
      tabIndex={-1}
    >
      <span className="italic text-red-error">Error loading {entity}</span>
      <Button
        icon={RefreshIcon}
        onClick={retry}
        size="sm"
        data-testid="retry-button"
      >
        Retry
      </Button>
    </div>
  );
}

/**
 * Checks if provided element's scroll is at the bottom.
 *
 * @param offset - Return true if the difference between the element's current
 *                 and maximum scroll position is below this value.
 *                 Defaults to 20.
 */
function elementScrollIsAtBottom(element: HTMLElement, offset = 20): boolean {
  const distanceToTop = element.scrollTop + element.clientHeight;
  const triggerPoint = element.scrollHeight - offset;
  return distanceToTop >= triggerPoint;
}

export type PaginatedMultiSelectProps<TResult, TSelect> = {
  result: PaginatedFetchResult<NonNullable<TResult>[]>;
  activeItem?: TResult;
  renderOption: (
    item: NonNullable<TResult>,
    ref?: MutableRef<HTMLElement | null>,
  ) => ComponentChildren;
  entity: FiltersEntity;
  buttonContent?: ComponentChildren;
  value: TSelect[];
  onChange: (newValue: TSelect[]) => void;
};

/**
 * A MultiSelect whose data is fetched from a paginated API.
 * It includes loading and error indicators, and transparently loads more data
 * while scrolling.
 */
export default function PaginatedMultiSelect<TResult, TSelect>({
  result,
  activeItem,
  entity,
  renderOption,
  buttonContent,
  value,
  onChange,
}: PaginatedMultiSelectProps<TResult, TSelect>) {
  const lastOptionRef = useRef<HTMLElement | null>(null);

  return (
    <MultiSelect
      disabled={result.isLoadingFirstPage}
      value={value}
      onChange={onChange}
      aria-label={`Select ${entity}`}
      containerClasses="!w-auto min-w-44"
      buttonContent={buttonContent}
      data-testid={`${entity}-select`}
      onListboxScroll={e => {
        if (elementScrollIsAtBottom(e.target as HTMLUListElement)) {
          result.loadNextPage();
        }
      }}
    >
      <MultiSelect.Option
        value={undefined}
        elementRef={
          !activeItem && (!result.data || result.data.length === 0)
            ? lastOptionRef
            : undefined
        }
      >
        All {entity}
      </MultiSelect.Option>
      {activeItem ? (
        renderOption(activeItem, lastOptionRef)
      ) : (
        <>
          {result.data?.map((item, index, list) =>
            renderOption(
              item,
              list.length - 1 === index ? lastOptionRef : undefined,
            ),
          )}
          {result.isLoading && <LoadingOption entity={entity} />}
          {result.error && (
            <LoadingError
              entity={entity}
              retry={() => {
                // Focus last option before retrying, to avoid the listbox to
                // be closed:
                // - Starting the fetch retry will cause the result to no
                //   longer be in the error state, hence the Retry button will
                //   be umounted.
                // - If the retry button had focus when unmounted, the focus
                //   would revert to the document body.
                // - Since the body is outside the select dropdown, this would
                //   cause the select dropdown to auto-close.
                // - To avoid this we focus a different element just before
                //   initiating the retry.
                lastOptionRef.current?.focus();
                result.retry();
              }}
            />
          )}
        </>
      )}
    </MultiSelect>
  );
}
