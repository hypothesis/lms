import type { DataTableProps, Order } from '@hypothesis/frontend-shared';
import { DataTable } from '@hypothesis/frontend-shared';
import { useOrderedRows } from '@hypothesis/frontend-shared';
import type { OrderDirection } from '@hypothesis/frontend-shared/lib/types';
import { useMemo, useState } from 'preact/hooks';
import { useLocation } from 'wouter-preact';

export type OrderableActivityTableColumn<T> = {
  field: keyof T;
  label: string;
  initialOrderDirection?: OrderDirection;
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
 */
export default function OrderableActivityTable<T>({
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
        classes: index === 0 ? 'lg:w-[60%] md:w-[45%]' : undefined,
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
