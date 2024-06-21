import { useMemo } from 'preact/hooks';

import { formatDateTime } from '../../utils/date';

export type FormattedDateProps = {
  /** Date in ISO format */
  date: string;
};

/**
 * Formats a date for current user's locale, and shows it in a non-wrapping
 * container
 */
export default function FormattedDate({ date }: FormattedDateProps) {
  const formattedDate = useMemo(() => formatDateTime(new Date(date)), [date]);
  return <div className="whitespace-nowrap">{formattedDate}</div>;
}
