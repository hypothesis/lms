/**
 * A naive regex matcher for a VBID in a URL-like string. The matcher looks
 * for a VitalSource book ID (VBID) in the string formatted as `books/<bookID>`.
 *
 * `bookID` may be of any length, but must consist only of upper-case alpha and
 * numeric characters, or dashes (`-`).
 *
 * The rest of the URL string other than `books/<bookID>` is ignored/irrelevant.
 *
 * Examples:
 * - https://bookshelf.vitalsource.com/#/books/12345678 -> '12345678'
 * - https://bookshelf.vitalsource.com/#/books/12345678/foo/bar -> '12345678'
 * - https://bookshelf.vitalsource.com/#/books/1A2345678Q-9 -> '1A2345678Q-9'
 * - books/BANANAS-47/other-parts-ignored -> 'BANANAS-47'
 *
 * @param {string} url
 * @returns {string|null} VBID, or `null` if nothing looks like a VBID in `url`
 */
export function bookIDFromURL(url) {
  const bookIdPattern = /books\/([0-9A-Z-]+)(\/|$)/;
  const matches = url.match(bookIdPattern);
  if (!matches) {
    return null;
  }
  return matches[1];
}
