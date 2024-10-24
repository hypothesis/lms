/**
 * Functions for working with EPUB Canonical Fragment Identifiers.
 *
 * See https://idpf.org/epub/linking/cfi/.
 */

/**
 * Strip assertions from a Canonical Fragment Identifier.
 *
 * Assertions are `[...]` enclosed sections which act as checks on the validity
 * of numbers but do not affect the sort order.
 *
 * @example
 *   stripCFIAssertions("/6/14[chap05ref]") // returns "/6/14"
 */
export function stripCFIAssertions(cfi: string): string {
  // Fast path for CFIs with no assertions.
  if (!cfi.includes('[')) {
    return cfi;
  }

  let result = '';

  // Has next char been escaped?
  let escaped = false;

  // Are we in a `[...]` assertion section?
  let inAssertion = false;

  for (const ch of cfi) {
    if (!escaped && ch === '^') {
      escaped = true;
      continue;
    }

    if (!escaped && ch === '[') {
      inAssertion = true;
    } else if (!escaped && inAssertion && ch === ']') {
      inAssertion = false;
    } else if (!inAssertion) {
      result += ch;
    }

    escaped = false;
  }

  return result;
}

/**
 * Return a slice of `cfi` up to the first step indirection [1], with assertions
 * removed.
 *
 * A typical CFI consists of a path within the table of contents to indicate
 * a content document, a step indirection ("!"), then the path of an element
 * within the content document. For such a CFI, this function will retain only
 * the content document path.
 *
 * [1] https://idpf.org/epub/linking/cfi/#sec-path-indirection
 *
 * @example
 *   documentCFI('/6/152[;vnd.vst.idref=ch13_01]!/4/2[ch13_sec_1]') // Returns "/6/152"
 */
export function documentCFI(cfi: string): string {
  const stripped = stripCFIAssertions(cfi);
  const sepIndex = stripped.indexOf('!');
  return sepIndex === -1 ? stripped : stripped.slice(0, sepIndex);
}
