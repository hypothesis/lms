/**
 * Test whether a value looks like a DOI.
 *
 * See https://en.wikipedia.org/wiki/Digital_object_identifier#Nomenclature_and_syntax.
 *
 * @param {string} value
 */
function isDOI(value) {
  return /^10.([0-9]+\.?)+\/.*/.test(value);
}

/**
 * Extract the JSTOR article ID or DOI from a form field value.
 *
 * Accepts input in various forms:
 *
 * - A numeric ID (1234)
 * - A DOI (10.2307/1234)
 * - A canonical URL for a JSTOR article (eg. http[s]://www.jstor.org/stable/<articleID>
 *   OR http[s]://www.jstor.org/stable/<doiPrefix>/<doiSuffix>)
 * - A URL for a JSTOR article that has being proxied through an institution's
 *   EZProxy or similar service (eg. https://www-jstor-org.myuni.edu/stable/1234).
 *
 * Return `null` if the input does not match any of the recognized formats.
 *
 * @param {string} value
 * @returns {string|null}
 */
export function articleIdFromUserInput(value) {
  // Plain JSTOR article ID
  if (/^[0-9a-z.]+$/.test(value)) {
    return value;
  }

  if (isDOI(value)) {
    return value;
  }

  // Try matching input as a URL containing a JSTOR article ID or DOI
  let testURL;
  try {
    testURL = new URL(value);
  } catch (e) {
    return null;
  }

  // Split path and remove any empty entries representing leading or trailing slashes
  const pathSegments = testURL.pathname.split('/').filter(segment => !!segment);

  // Test if this looks like the main JSTOR site (www.jstor.org) or the main
  // JSTOR site accessed via a proxy (eg. www-jstor-org.library.someuni.edu).
  //
  // See https://gist.github.com/robertknight/5110065b0ad536093f466a60aed0ae23
  // for more examples of real proxied URLs.
  const isJSTORHost = /\bwww\Wjstor\Worg\b/.test(testURL.hostname);

  if (isJSTORHost && pathSegments[0] === 'stable') {
    // The path is expected to be in one of these formats:
    //
    // /stable/{article_id}
    // /stable/{doi_prefix}/{doi_suffix}
    // /stable/pdf/{article_id}.pdf
    // /stable/pdf/{doi_prefix}/{doi_suffix}.pdf
    //
    const idSegments =
      pathSegments[1] === 'pdf'
        ? pathSegments.slice(2).map(s => s.replace(/\.pdf$/, ''))
        : pathSegments.slice(1);

    if (idSegments.length === 1) {
      return idSegments[0];
    } else if (idSegments.length === 2) {
      const doi = idSegments.join('/');
      if (isDOI(doi)) {
        return doi;
      }
    } else {
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
