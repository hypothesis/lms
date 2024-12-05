import {
  decayingInterval,
  formatRelativeDate,
  formatDateTime,
} from '@hypothesis/frontend-shared';
import { useEffect, useMemo, useState } from 'preact/hooks';

export type RelativeTimeProps = {
  /** The reference date-time, in ISO format */
  dateTime: string;

  /**
   * Whether a `title` attribute with the absolute date should be added.
   * Defaults to `true`.
   */
  withTitle?: boolean;
};

/**
 * Displays a date as a time relative to `now`, making sure it is updated at
 * appropriate intervals
 */
export default function RelativeTime({
  dateTime,
  withTitle = true,
}: RelativeTimeProps) {
  const [now, setNow] = useState(() => new Date());
  const absoluteDate = useMemo(
    () =>
      withTitle
        ? formatDateTime(dateTime, { includeWeekday: true })
        : undefined,
    [dateTime, withTitle],
  );
  const relativeDate = useMemo(
    () => formatRelativeDate(new Date(dateTime), now),
    [dateTime, now],
  );

  // Refresh relative timestamp, at a frequency appropriate for the age.
  useEffect(() => {
    return decayingInterval(dateTime, () => setNow(new Date()));
  }, [dateTime]);

  return (
    <time dateTime={dateTime} title={absoluteDate}>
      {relativeDate}
    </time>
  );
}
