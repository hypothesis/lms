/**
 * Coerce a string value from an input field to an numeric value.
 * If the value can't be properly cast, then it will remain a string.
 *
 * @param {string} value - The value to attempt to translate
 * @return {number|string} - Translated value or original if not translated
 */
function translateToNumber(value) {
  if (value.toString().trim().length === 0) {
    // don't translate a string with only tabs or spaces
    return value;
  }
  const translated = Number(value);
  if (isNaN(translated)) {
    return value;
  } else {
    return translated;
  }
}

/**
 * The validator will ensure the value is:
 * - a numeric type
 * - between or equal to the the range of [0 - 10]
 * -
 * @param {number} value - Value to test
 * @return {string|undefined} - Returns an error message or undefined if valid.
 */
function validateGrade(value) {
  if (typeof value !== 'number') {
    return 'Grade must be a valid number';
  } else if (value < 0 || value > 10) {
    return 'Grade must be between 0 and 10';
  } else {
    return undefined;
  }
}

export { translateToNumber, validateGrade };
