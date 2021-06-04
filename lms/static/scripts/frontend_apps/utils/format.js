/**
 * Truncate a URL to be `maxLength` or fewer characters.
 *
 * If `url` needs to be shortened, `truncateURL` tries to preserve the most
 * informative parts of the URL using some simple heuristics.
 *
 * If `url` is not a valid URL, it is just shortened to the first `maxLength - 1`
 * characters.
 *
 * @param {string} url
 * @param {number} maxLength
 */
export function truncateURL(url, maxLength) {
  // The URL is progressively shortened in stages until its length becomes <=
  // `maxLength` and then returned:
  //
  // 1. https://example.com/foobar/baz/quux?query#fragment
  // 2. example.com/foobar/baz/quux?query#fragment (strip protocol)
  // 3. example.com/foobar/baz/quux (strip query and fragment)
  // 4. example.com/…/baz/quux (elide path segments incrementally)
  // 5. example.com/…/quux
  // 6. example.com/…/qu… (elide end of URL)

  if (url.length <= maxLength) {
    return url;
  }

  const urlWithoutScheme = url.replace(/^[^:]+:\/\//, '');
  if (urlWithoutScheme.length <= maxLength) {
    return urlWithoutScheme;
  }

  let parsed;
  try {
    parsed = new URL(url);
  } catch {
    return url.slice(0, maxLength - 1) + '…';
  }

  const hostname = parsed.hostname;
  const pathSegments = parsed.pathname.split('/');
  let pathTruncated = false;

  const getCandidate = () =>
    hostname + (pathTruncated ? '/…/' : '') + pathSegments.join('/');
  while (pathSegments.length > 1 && getCandidate().length > maxLength) {
    pathTruncated = true;
    pathSegments.shift();
  }

  let result = getCandidate();
  if (result.length > maxLength) {
    result = result.slice(0, maxLength - 1) + '…';
  }

  return result;
}
