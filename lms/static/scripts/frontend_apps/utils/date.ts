/**
 * Return a datetime string that `Date` reliably parses as UTC.
 *
 * Backend datetimes come in two shapes: naive strings with no timezone
 * ("2026-07-08T23:59:29.622705") which are implicitly UTC, and strings with
 * an explicit offset ("2026-07-08T23:59:29.622705+00:00") produced by
 * timezone-aware columns. Appending "Z" to a string that already has an
 * offset (or a "Z") produces an invalid date, so only append it to naive
 * strings.
 */
export function assumeUTC(date: string): string {
  return /Z$|[+-]\d{2}:\d{2}$/.test(date) ? date : date + 'Z';
}
