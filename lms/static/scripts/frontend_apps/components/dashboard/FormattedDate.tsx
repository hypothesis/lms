import { formatDateTime } from '@hypothesis/frontend-shared';
import { useMemo } from 'preact/hooks';

export type FormattedDateProps = {
  /** Date in ISO format */
  date: string;
};

/**
 * Formats a date for current user's locale, and shows it in a non-wrapping
 * container
 */
export default function FormattedDate({ date }: FormattedDateProps) {
  const formattedDate = useMemo(() => formatDateTime(date), [date]);
  return <div className="whitespace-nowrap">{formattedDate}</div>;
}
