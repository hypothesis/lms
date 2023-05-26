import { LinkButton } from '@hypothesis/frontend-shared';
import type { ComponentChildren } from 'preact';

export type BreadcrumbsProps<Item> = {
  items: Item[];
  onSelectItem: (i: Item) => void;
  renderItem: (i: Item) => ComponentChildren;
};

/**
 * Render a collection of breadcrumbs. All but the last breadcrumb is clickable,
 * and will invoke the `onSelectItem` when clicked.
 */
export default function Breadcrumbs<Item>({
  items,
  onSelectItem,
  renderItem,
}: BreadcrumbsProps<Item>) {
  if (!items.length) {
    return null;
  }
  const breadcrumbs = items.slice(0, -1);
  const currentItem = items[items.length - 1];
  return (
    <ul className="flex flex-wrap leading-none">
      {breadcrumbs.map((item, idx) => (
        <li className="flex" key={idx}>
          <LinkButton onClick={() => onSelectItem(item)} underline="none">
            {renderItem(item)}
          </LinkButton>
          <span className="mx-2">›</span>
        </li>
      ))}
      <li>
        <LinkButton disabled underline="none">
          {renderItem(currentItem)}
        </LinkButton>
      </li>
    </ul>
  );
}
