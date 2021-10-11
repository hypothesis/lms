/**
 * Attempt to parse a book ID out of a string. A book ID may be either a VBID
 * (VitalSource Book ID) or an ISBN.
 *
 * A valid input string has one of two possible patterns:
 * 1. A URL- or path-like string that contains a substring
 *   'books/<bookID>', OR
 * 2. A string consisting _only_ of a bookID
 *
 * A book ID may be of any length, but must consist only of upper-case alpha and
 * numeric characters, or dashes (`-`).
 *
 * Examples:
 * - https://bookshelf.vitalsource.com/#/books/12345678 -> '12345678'
 * - https://bookshelf.vitalsource.com/#/books/12345678/foo/bar -> '12345678'
 * - https://bookshelf.vitalsource.com/#/books/1A2345678Q-9 -> '1A2345678Q-9'
 * - https://bookshelf.vitalsource.com/#/foo/1P44349834/books/1A2345678Q-9 -> '1A2345678Q-9'
 * - books/BANANAS-47/other-parts-ignored -> 'BANANAS-47'
 * - 12345678X -> '12345678X'
 *
 * @param {string} input
 * @returns {string|null} bookID, or `null` if nothing looks like a bookID in
 *  `input`
 */
export function extractBookID(input) {
  const urlMatches = input.match(/books\/([0-9A-Z-]+)(\/|$)/);
  if (urlMatches) {
    return urlMatches[1];
  }
  const bookIDMatches = input.match(/^([0-9A-Z-]+)$/);
  if (bookIDMatches) {
    return bookIDMatches[1];
  }
  return null;
}
