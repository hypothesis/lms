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
 * @returns bookID, or `null` if nothing looks like a bookID in
 *  `input`
 */
export function extractBookID(input: string): string | null {
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

/**
 * Report whether a page range is valid. A page range is considered valid if:
 *
 *  - The start and end are specified
 *  - The start and end pages are numbers, and start >= end
 *  - Either the start or end is not a number
 *
 * The last condition handles the cases where books have some page numbers that
 * are not numeric (eg. roman numerals). In that case we don't try to compare
 * them and just trust the user.
 */
export function isPageRangeValid(start: string, end: string): boolean {
  if (!start || !end) {
    return false;
  }

  const startInt = parseInt(start);
  const endInt = parseInt(end);
  if (isNaN(startInt) || isNaN(endInt)) {
    return true;
  }

  return startInt >= 1 && endInt >= startInt;
}
