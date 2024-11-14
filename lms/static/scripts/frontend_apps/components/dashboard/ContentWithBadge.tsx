import type { ComponentChildren } from 'preact';

export type ContentWithBadgeProps = {
  children: ComponentChildren;
  count: number;

  /**
   * Indicates the count is a lower-bound on the total number of items, as
   * opposed to an exact value.
   * Defaults to false.
   */
  hasMoreItems?: boolean;
};

/**
 * Display content next to a badge containing a count of items.
 */
export default function ContentWithBadge({
  children,
  count,
  hasMoreItems = false,
}: ContentWithBadgeProps) {
  // We want to give a special treatment to the value 100 when there are more
  // items, falling back to 99 to avoid using too much space.
  // This will be the most common use case for paginated results, before users
  // open the list and start scrolling down, so we want to keep it as long as
  // possible.
  const displayCount = count === 100 && hasMoreItems ? 99 : count;

  return (
    <div className="flex gap-x-2 items-center justify-between">
      {children}
      <div
        className="px-2 -my-1 py-1 rounded font-bold bg-grey-3 text-grey-7"
        data-testid="count-badge"
      >
        {displayCount}
        {hasMoreItems && '+'}
      </div>
    </div>
  );
}
