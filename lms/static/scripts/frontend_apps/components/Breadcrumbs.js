import { LinkButton } from '@hypothesis/frontend-shared';
import { createElement } from 'preact';

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
 * @returns {Item}
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
  const breadcrumbs = items.slice(0, -1);
  const currentItem = items[items.length - 1];
  return (
    <ul className="Breadcrumbs hyp-u-layout-row">
      {breadcrumbs.map((item, idx) => (
        <li className="Breadcrumbs__crumb Breadcrumbs__crumb--path" key={idx}>
          <LinkButton onClick={() => onSelectItem(item)}>
            {renderItem(item)}
          </LinkButton>
          <span className="Breadcrumbs__crumb-divider">›</span>
        </li>
      ))}
      <li className="Breadcrumbs__crumb Breadcrumbs__crumb--current">
        <LinkButton disabled>{renderItem(currentItem)}</LinkButton>
      </li>
    </ul>
  );
}
