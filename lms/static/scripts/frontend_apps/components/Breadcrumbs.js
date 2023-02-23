import { LinkButton } from '@hypothesis/frontend-shared';

/**
 * @template Item
 * @typedef BreadcrumbProps
 * @prop {Item[]} items
 * @prop {(i: Item) => void} onSelectItem
 * @prop {(i: Item) => any} [renderItem]
 */

/**
 * @template Item
 * @param {Item} item
 */
const defaultRenderItem = item => item;

/**
 * Render a collection of breadcrumbs. All but the last breadcrumb is clickable,
 * and will invoke the `onSelectItem` when clicked.
 *
 * @template Item
 * @param {BreadcrumbProps<Item>} props
 */
export default function Breadcrumbs({
  items,
  onSelectItem,
  renderItem = defaultRenderItem,
}) {
  if (!items.length) {
    return null;
  }
  const breadcrumbs = items.slice(0, -1);
  const currentItem = items[items.length - 1];
  return (
    <ul className="flex flex-wrap leading-none">
      {breadcrumbs.map((item, idx) => (
        <li className="flex" key={idx}>
          <LinkButton onClick={() => onSelectItem(item)}>
            {renderItem(item)}
          </LinkButton>
          <span className="mx-2">›</span>
        </li>
      ))}
      <li>
        <LinkButton disabled>{renderItem(currentItem)}</LinkButton>
      </li>
    </ul>
  );
}
