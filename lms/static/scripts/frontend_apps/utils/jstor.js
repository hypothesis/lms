/**
 * Extract the JSTOR article ID from a URL.
 *
 * Accepts URLs of the form:
 * - http[s]://www.jstor.org/stable/<articleID> OR
 * - http[s]://www.jstor.org/stable/<doiPrefix>/<doiSuffix>
 *
 * (Query string is ignored on provided URLs)
 *
 * and returns, respectively:
 * - <articleID> OR
 * - <doiPrefix>/<doiSuffix>
 *
 * Return `null` if provided string is not a URL or does not match one of the
 * accepted formats.
 *
 * @param {string} url
 * @returns {string|null}
 */
export function articleIdFromURL(url) {
  let testURL;

  try {
    testURL = new URL(url);
  } catch (e) {
    return null;
  }

  // Split path and remove any empty entries representing leading or trailing slashes
  const pathSegments = testURL.pathname.split('/').filter(segment => !!segment);

  if (testURL.hostname === 'www.jstor.org' && pathSegments[0] === 'stable') {
    pathSegments.shift();
    switch (pathSegments.length) {
      case 1:
        // Supplied URL is of the format
        // http[s]://www.jstor.org/stable/<articleID>
        return pathSegments[0];
      case 2:
        // Supplied URL is of the format
        // http[s]://www.jstor.org/stable/<doiPrefix>/<doiSuffix>
        // Ensure <doiPrefix> starts with `10.` and contains only digits or
        // periods
        if (pathSegments[0].match(/10\.[\d.]*$/)) {
          return `${pathSegments[0]}/${pathSegments[1]}`;
        }
        break;
      default:
        return null;
    }
  }

  return null;
}

/**
 * @param {string} articleId
 */
export function jstorURLFromArticleId(articleId) {
  return `jstor://${articleId}`;
}
