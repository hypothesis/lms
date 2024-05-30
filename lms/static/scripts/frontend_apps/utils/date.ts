/**
 * Map of stringified `DateTimeFormatOptions` to cached `DateTimeFormat` instances.
 */
let formatters = new Map<string, Intl.DateTimeFormat>();

/**
 * Clears the cache of formatters.
 */
export function clearFormatters() {
  formatters = new Map<string, Intl.DateTimeFormat>();
}

type IntlType = typeof window.Intl;

/**
 * Return date string formatted with `options`.
 *
 * This is a caching wrapper for `Intl.DateTimeFormat.format`, useful because
 * constructing a `DateTimeFormat` is expensive.
 *
 * @param Intl - Test seam. JS `Intl` API implementation.
 */
function format(
  date: Date,
  options: Intl.DateTimeFormatOptions,
  /* istanbul ignore next */
  Intl: IntlType = window.Intl,
): string {
  const key = JSON.stringify(options);
  let formatter = formatters.get(key);
  if (!formatter) {
    formatter = new Intl.DateTimeFormat(undefined, options);
    formatters.set(key, formatter);
  }
  return formatter.format(date);
}

/**
 * Formats a date as an absolute string in a human-readable format.
 *
 * The exact format will vary depending on the locale, but the verbosity will
 * be consistent across locales. In en-US for example this will look like:
 *
 *  "Dec 17, 2017, 10:00 AM"
 *
 * @param Intl - Test seam. JS `Intl` API implementation.
 */
export function formatDateTime(date: Date, Intl?: IntlType): string {
  return format(
    date,
    {
      year: 'numeric',
      month: 'short',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    },
    Intl,
  );
}
