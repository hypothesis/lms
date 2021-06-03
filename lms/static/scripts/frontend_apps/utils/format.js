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
  if (url.length <= maxLength) {
    return url;
  }

  // Strip the protocol and return if that is sufficient.
  const urlWithoutScheme = url.replace(/^[^:]+:\/\//, '');
  if (urlWithoutScheme.length <= maxLength) {
    return urlWithoutScheme;
  }

  // Strip the query string and fragment, then continue removing path segments
  // until the result is shorter than `maxLength`.
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

  // If the final URL is still too long, just elide it.
  let result = getCandidate();
  if (result.length > maxLength) {
    result = result.slice(0, maxLength - 1) + '…';
  }

  return result;
}
