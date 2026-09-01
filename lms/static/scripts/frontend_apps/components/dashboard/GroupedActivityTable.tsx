import {
  ArrowDownIcon,
  ArrowUpIcon,
  OrderableIcon,
  SpinnerSpokesIcon,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  useOrderedRows,
} from '@hypothesis/frontend-shared';
import type { Order } from '@hypothesis/frontend-shared/lib/types';
import classnames from 'classnames';
import type { ComponentChildren } from 'preact';
import { useMemo, useState } from 'preact/hooks';

import type { OrderableActivityTableColumn } from './OrderableActivityTable';

export type GroupedActivityTableProps<T> = {
  title: string;
  rows: T[];
  columns: OrderableActivityTableColumn<T>[];
  defaultOrderField: keyof T;

  /**
   * Render one cell. Defaults to the raw value of the field, as `DataTable`
   * does.
   */
  renderItem?: (row: T, field: keyof T) => ComponentChildren;
  loading?: boolean;
  emptyMessage?: ComponentChildren;
};

type ColumnGroup = {
  label?: string;
  span: number;
};

/**
 * Runs of adjacent columns which share a group, in display order.
 *
 * The spans add up to the number of columns, so the group row always covers
 * exactly the same width as the column row below it.
 */
function columnGroups<T>(
  columns: OrderableActivityTableColumn<T>[],
): ColumnGroup[] {
  const groups: ColumnGroup[] = [];
  let current: ColumnGroup | undefined;

  for (const { group } of columns) {
    if (current && current.label === group) {
      current.span += 1;
    } else {
      current = { label: group, span: 1 };
      groups.push(current);
    }
  }

  return groups;
}

/**
 * Indices of the columns which open a group, excluding the first.
 *
 * These carry the rule that separates one group from the next, so a reader can
 * tell where a phase's metrics end and the next phase's begin.
 */
function groupBoundaries(groups: ColumnGroup[]): Set<number> {
  const boundaries = new Set<number>();
  let index = 0;

  for (const { span } of groups) {
    if (index > 0) {
      boundaries.add(index);
    }
    index += span;
  }

  return boundaries;
}

/** Separates a group from the one before it. */
const GROUP_RULE = 'border-l-2 border-l-grey-5';

/**
 * Activity table whose columns are displayed under a shared header, for views
 * which repeat the same metrics for more than one window of time.
 *
 * This is the grouped-header counterpart of `OrderableActivityTable`, which
 * renders a flat list of columns via `DataTable`. `DataTable` builds its own
 * single header row, so a second one has to be assembled from the table
 * primitives instead.
 */
export default function GroupedActivityTable<T>({
  title,
  rows,
  columns,
  defaultOrderField,
  renderItem = (row, field) => row[field] as ComponentChildren,
  loading = false,
  emptyMessage,
}: GroupedActivityTableProps<T>) {
  const [order, setOrder] = useState<Order<keyof T>>({
    field: defaultOrderField,
    direction: 'ascending',
  });
  // The caller can change its column set — a variant which repeats metrics per
  // window drops a group when the data behind it goes away — and the ordered
  // column can go with it. Ordering by a field no column holds sorts nothing and
  // leaves no header marked, so fall back to the default instead.
  const effectiveOrder = useMemo(
    () =>
      columns.some(({ field }) => field === order.field)
        ? order
        : { field: defaultOrderField, direction: 'ascending' as const },
    [columns, defaultOrderField, order],
  );
  const orderedRows = useOrderedRows(rows, effectiveOrder);
  const groups = useMemo(() => columnGroups(columns), [columns]);
  const boundaries = useMemo(() => groupBoundaries(groups), [groups]);
  const hasGroups = useMemo(
    () => columns.some(({ group }) => !!group),
    [columns],
  );
  const showEmptyMessage = !loading && orderedRows.length === 0;

  const toggleOrder = ({
    field,
    initialOrderDirection = 'ascending',
  }: OrderableActivityTableColumn<T>) => {
    const direction =
      effectiveOrder.field !== field
        ? initialOrderDirection
        : effectiveOrder.direction === 'ascending'
          ? 'descending'
          : 'ascending';

    setOrder({
      field,
      direction,
      // Every column starts with nulls last, and moves them first when the
      // order direction changes
      nullsLast: direction === initialOrderDirection,
    });
  };

  return (
    // `striped` is off to match the `DataTable` the other dashboard tables use
    <Table title={title} grid stickyHeader striped={false}>
      {/*
        Column widths go here rather than on a header cell: with `table-fixed`
        the layout is taken from the first row, which is the group row, and its
        cells span several columns.
       */}
      <colgroup>
        {columns.map(({ field, width }) => (
          <col key={String(field)} className={width} />
        ))}
      </colgroup>
      <TableHead>
        {hasGroups && (
          <TableRow>
            {groups.map(({ label, span }, index) => (
              <TableCell
                key={`${label ?? ''}-${index}`}
                colSpan={span}
                classes={classnames({ [GROUP_RULE]: index > 0 })}
              >
                {/*
                  The alignment goes on a wrapper rather than on the cell:
                  `TableCell` sets `text-left` on every header cell, and it wins
                  over a utility class passed in `classes`.
                 */}
                <div
                  className={classnames('text-center', {
                    'font-bold': !!label,
                  })}
                >
                  {label}
                </div>
              </TableCell>
            ))}
          </TableRow>
        )}
        <TableRow>
          {columns.map((column, index) => {
            const { field, label, group } = column;
            const isOrdered = effectiveOrder.field === field;

            return (
              <TableCell
                key={String(field)}
                classes={classnames({ [GROUP_RULE]: boundaries.has(index) })}
                aria-sort={isOrdered ? effectiveOrder.direction : undefined}
              >
                <button
                  className="flex items-center gap-x-1 w-full"
                  onClick={() => toggleOrder(column)}
                  // The group is in a cell of its own row, which `TableCell`
                  // scopes to a single column, so a column of a group carries
                  // its name in its own accessible name. Without it the two
                  // `Annotations` of a two-phase table are indistinguishable.
                  aria-label={group ? `${group} ${label}` : undefined}
                >
                  <div className="grow">{label}</div>
                  <div className="flex items-center" aria-hidden>
                    {/*
                      Always displayed, as `DataTable` does: hiding it until
                      hover would reveal it on every column at once, because the
                      element carrying `group` is the row, not the cell.
                     */}
                    {!isOrdered && <OrderableIcon className="text-grey-5" />}
                    {isOrdered &&
                      (effectiveOrder.direction === 'ascending' ? (
                        <ArrowUpIcon />
                      ) : (
                        <ArrowDownIcon />
                      ))}
                  </div>
                </button>
              </TableCell>
            );
          })}
        </TableRow>
      </TableHead>
      <TableBody>
        {!loading &&
          orderedRows.map((row, index) => (
            <TableRow key={index}>
              {columns.map(({ field }, columnIndex) => (
                <TableCell
                  key={String(field)}
                  classes={classnames({
                    [GROUP_RULE]: boundaries.has(columnIndex),
                  })}
                >
                  {renderItem(row, field)}
                </TableCell>
              ))}
            </TableRow>
          ))}
        {(loading || showEmptyMessage) && (
          <TableRow>
            <TableCell colSpan={columns.length}>
              <div className="flex justify-center">
                {loading ? <SpinnerSpokesIcon /> : emptyMessage}
              </div>
            </TableCell>
          </TableRow>
        )}
      </TableBody>
    </Table>
  );
}
