import classnames from 'classnames';
import { createElement } from 'preact';
import { useRef } from 'preact/hooks';
import propTypes from 'prop-types';

/**
 * Return the next item to select when advancing the selection by `step` items
 * forwards (if positive) or backwards (if negative).
 *
 * @template Item
 * @param {Item[]} items
 * @param {Item} currentItem
 * @param {number} step
 */
function nextItem(items, currentItem, step) {
  const index = items.indexOf(currentItem);
  if (index < 0) {
    return items[0];
  }

  if (index + step < 0) {
    return items[0];
  }

  if (index + step >= items.length) {
    return items[items.length - 1];
  }

  return items[index + step];
}

/**
 * @typedef TableColumn
 * @prop {string} label - Header label for the column
 * @prop {string} className - Additional classes for the column's `<th>` element
 */

/**
 * @template Item
 * @typedef TableProps
 * @prop {string} accessibleLabel - An accessible label for the table
 * @prop {TableColumn[]} columns - The columns to display in this table
 * @prop {Item[]} items -
 *   The items to display in this table, one per row. `renderItem` defines how
 *   information from each item is represented as a series of table cells.
 * @prop {(it: Item, selected: boolean) => any} renderItem -
 *   A function called to render each item as the contents of a table row.
 *   The result should be a list of `<td>` elements (one per column) wrapped inside a Fragment.
 * @prop {Item|null} selectedItem - The currently selected item from `items`
 * @prop {(it: Item) => any} onSelectItem -
 *   Callback invoked when the user changes the selected item
 * @prop {(it: Item) => any} onUseItem -
 *   Callback invoked when a user chooses to use an item by double-clicking it
 *   or pressing Enter while it is selected
 */

/**
 * An interactive table of items with a sticky header.
 *
 * @template Item
 * @param {TableProps<Item>} props
 */
export default function Table({
  accessibleLabel,
  columns,
  items,
  onSelectItem,
  onUseItem,
  renderItem,
  selectedItem,
}) {
  const rowRefs = useRef(/** @type {(HTMLElement|null)[]} */ ([]));

  const focusAndSelectItem = item => {
    const itemIndex = items.indexOf(item);
    const rowEl = rowRefs.current[itemIndex];
    if (rowEl) {
      rowEl.focus();
    }
    onSelectItem(item);
  };

  const onKeyDown = event => {
    let handled = false;
    if (event.key === 'Enter') {
      handled = true;
      if (selectedItem) {
        onUseItem(selectedItem);
      }
    } else if (event.key === 'ArrowUp') {
      handled = true;
      focusAndSelectItem(nextItem(items, selectedItem, -1));
    } else if (event.key === 'ArrowDown') {
      handled = true;
      focusAndSelectItem(nextItem(items, selectedItem, 1));
    }
    if (handled) {
      event.preventDefault();
      event.stopPropagation();
    }
  };

  return (
    <div className="Table__wrapper">
      <table
        aria-label={accessibleLabel}
        className="Table__table"
        tabIndex={0}
        role="grid"
        onKeyDown={onKeyDown}
      >
        <thead className="Table__head">
          <tr>
            {columns.map(column => (
              <th
                key={column.label}
                className={classnames('Table__head-cell', column.className)}
                scope="col"
              >
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="Table__body">
          {items.map((item, index) => (
            <tr
              aria-selected={selectedItem === item}
              key={index}
              className={classnames({
                Table__row: true,
                'is-selected': selectedItem === item,
              })}
              onMouseDown={() => onSelectItem(item)}
              onClick={() => onSelectItem(item)}
              onDblClick={() => onUseItem(item)}
              ref={node => (rowRefs.current[index] = node)}
              tabIndex={-1}
            >
              {renderItem(item, selectedItem === item)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

Table.propTypes = {
  accessibleLabel: propTypes.string.isRequired,
  columns: propTypes.arrayOf(
    propTypes.shape({
      label: propTypes.string,
      className: propTypes.string,
    })
  ).isRequired,
  items: propTypes.arrayOf(propTypes.any).isRequired,
  renderItem: propTypes.func.isRequired,
  selectedItem: propTypes.any,
  onSelectItem: propTypes.func,
  onUseItem: propTypes.func,
};
