import type { DataTableProps, Order } from '@hypothesis/frontend-shared';
import { DataTable } from '@hypothesis/frontend-shared';
import { useOrderedRows } from '@hypothesis/frontend-shared';
import type { OrderDirection } from '@hypothesis/frontend-shared/lib/types';
import { useMemo, useState } from 'preact/hooks';

import type { BaseDashboardStats } from '../../api-types';

export type OrderableActivityTableProps<T extends BaseDashboardStats> = Pick<
  DataTableProps<T>,
  'emptyMessage' | 'rows' | 'renderItem' | 'loading' | 'title'
> & {
  columnNames: Partial<Record<keyof T, string>>;
  defaultOrderField: keyof T;
};

/**
 * List of columns which should start sorted in descending order.
 *
 * This is because for numeric columns ("annotations" and "replies") users will
 * usually want to see the higher values first.
 * Similarly, for date columns ("last_activity") users will want to see most
 * recent values first.
 */
const descendingOrderColumns: readonly string[] = [
  'last_activity',
  'annotations',
  'replies',
];

/**
 * Annotation activity table for dashboard views. Includes built-in support for
 * sorting columns.
 */
export default function OrderableActivityTable<T extends BaseDashboardStats>({
  defaultOrderField,
  rows,
  columnNames,
  ...restOfTableProps
}: OrderableActivityTableProps<T>) {
  const [order, setOrder] = useState<Order<keyof T>>({
    field: defaultOrderField,
    direction: 'ascending',
  });
  const orderedRows = useOrderedRows(rows, order);
  const columns = useMemo(
    () =>
      Object.entries(columnNames).map(([field, label], index) => ({
        field: field as keyof T,
        label: label as string,
        classes: index === 0 ? 'w-[60%]' : undefined,
      })),
    [columnNames],
  );
  // Map of column name to initial sort order
  const orderableColumns = useMemo(
    () =>
      (Object.keys(columnNames) as Array<keyof T>).reduce<
        Partial<Record<keyof T, OrderDirection>>
      >((acc, columnName) => {
        acc[columnName] =
          typeof columnName === 'string' &&
          descendingOrderColumns.includes(columnName)
            ? 'descending'
            : 'ascending';
        return acc;
      }, {}),
    [columnNames],
  );

  return (
    <DataTable
      grid
      striped={false}
      columns={columns}
      rows={orderedRows}
      orderableColumns={orderableColumns}
      order={order}
      onOrderChange={setOrder}
      {...restOfTableProps}
    />
  );
}
