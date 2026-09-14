import type { DataTableProps, Order } from '@hypothesis/frontend-shared';
import { DataTable } from '@hypothesis/frontend-shared';
import { useOrderedRows } from '@hypothesis/frontend-shared';
import type { OrderDirection } from '@hypothesis/frontend-shared/lib/types';
import classnames from 'classnames';
import { useMemo, useState } from 'preact/hooks';
import { useLocation } from 'wouter-preact';

import GroupedActivityTable from './GroupedActivityTable';

export type OrderableActivityTableColumn<T> = {
  field: keyof T;
  label: string;
  initialOrderDirection?: OrderDirection;

  /**
   * Header this column is displayed under, for the views which repeat the same
   * metrics for more than one window of time.
   *
   * The label identifies the group: the header spans the run of adjacent columns
   * which declare the same one, so the columns of a group have to be adjacent
   * and two different groups must not share a label — they would be displayed
   * under a single header spanning both.
   *
   * Only `GroupedActivityTable` renders these; `OrderableActivityTable` builds
   * a flat header row and ignores them.
   */
  group?: string;

  /**
   * Width of this column, as a utility class.
   *
   * The table lays its columns out with `table-fixed`, which divides the width
   * evenly between the columns which do not declare one. Only declare a width
   * for a column whose content does not fit an even share.
   *
   * Only `GroupedActivityTable` honours this; the `DataTable` path sizes its
   * columns itself.
   */
  width?: string;
};

export type OrderableActivityTableProps<T> = Pick<
  DataTableProps<T>,
  'emptyMessage' | 'rows' | 'renderItem' | 'loading' | 'title'
> & {
  columns: OrderableActivityTableColumn<T>[];
  defaultOrderField: keyof T;

  /**
   * Allows to define a URL to navigate to when a row is confirmed via
   * double-click/Enter key press.
   */
  navigateOnConfirmRow?: (row: T) => string;
};

/**
 * Annotation activity table for dashboard views. Includes built-in support for
 * sorting columns.
 *
 * A caller whose columns declare a `group` gets the grouped-header table
 * instead, which builds its own header rows out of the table primitives. That
 * one does not have the keyboard navigation and row selection `DataTable`
 * brings, so `navigateOnConfirmRow` and grouped columns do not go together.
 */
export default function OrderableActivityTable<T>({
  columns,
  navigateOnConfirmRow,
  ...restOfTableProps
}: OrderableActivityTableProps<T>) {
  const hasGroups = useMemo(
    () => columns.some(({ group }) => !!group),
    [columns],
  );

  // `navigateOnConfirmRow` is left out of the grouped table on purpose rather
  // than spread into it: that one has no row confirmation to hook into, and
  // forwarding it would drop it silently.
  return hasGroups ? (
    <GroupedActivityTable columns={columns} {...restOfTableProps} />
  ) : (
    <FlatActivityTable
      columns={columns}
      navigateOnConfirmRow={navigateOnConfirmRow}
      {...restOfTableProps}
    />
  );
}

/** Activity table with a single header row, rendered by `DataTable`. */
function FlatActivityTable<T>({
  defaultOrderField,
  rows,
  columns,
  navigateOnConfirmRow,
  ...restOfTableProps
}: OrderableActivityTableProps<T>) {
  const [order, setOrder] = useState<Order<keyof T>>({
    field: defaultOrderField,
    direction: 'ascending',
  });
  const orderedRows = useOrderedRows(rows, order);
  const dataTableColumns = useMemo(
    () =>
      columns.map(({ field, label }, index) => ({
        field,
        label,
        classes: classnames({
          // For assignments with auto-grading, a fifth column is displayed.
          // In that case, we need to reserve less space for the first column,
          // otherwise the rest overflow.
          'lg:w-[55%] md:w-[45%]': index === 0 && columns.length < 5,
          'lg:w-[40%] md:w-[30%]': index === 0 && columns.length >= 5,
        }),
      })),
    [columns],
  );
  // Map of column name to initial sort order
  const orderableColumns = useMemo(
    () =>
      columns.reduce<Partial<Record<keyof T, OrderDirection>>>(
        (acc, { field, initialOrderDirection = 'ascending' }) => {
          acc[field] = initialOrderDirection;
          return acc;
        },
        {},
      ),
    [columns],
  );
  const [, navigate] = useLocation();

  return (
    <DataTable
      grid
      striped={false}
      columns={dataTableColumns}
      rows={orderedRows}
      orderableColumns={orderableColumns}
      order={order}
      onOrderChange={order =>
        setOrder({
          ...order,
          // Every column should start with nulls last, and move them first
          // when order direction changes
          nullsLast: order.direction === orderableColumns[order.field],
        })
      }
      onConfirmRow={
        navigateOnConfirmRow
          ? row => navigate(navigateOnConfirmRow(row))
          : undefined
      }
      {...restOfTableProps}
    />
  );
}
