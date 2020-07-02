/**
 * Coerce a string value from an input field to an numeric value.
 * If the value can't be properly cast, then it will remain a string.
 *
 * @param {string} originalValue - The value to attempt to translate
 * @return {number|string} - Translated value or original if not translated
 */
function formatToNumber(originalValue) {
  // Remove any trailing or leading tabs or spaces
  const value = originalValue.trim();
  if (value.length === 0) {
    // If its an empty string just return it so its
    // not converted to a 0.
    return originalValue;
  }
  const translated = Number(value);
  if (isNaN(translated)) {
    return originalValue;
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

/**
 * Return a scaled grade rounded to the same precision
 * as the original grade. This method eliminates precision
 * errors with floating point scaling.
 *
 * e.g. 0.66 will scale to 6.6 with a multiplier of 10
 *      0.667 will scale to 6.67  with a multiplier of 10
 *
 * @param {number} grade
 * @param {number} multiplier
 * @return {number}
 */
function scaleGrade(grade, multiplier) {
  const sGrade = grade.toString();
  if (sGrade.indexOf('.') < 0) {
    // no decimal value, just returns the scaled value
    return grade * multiplier;
  } else {
    const decimalDigitsLength = sGrade.split('.')[1].length;
    // scale and round to one less the number of decimal digits the grade had
    return (grade * multiplier).toFixed(decimalDigitsLength - 1);
  }
}

export { formatToNumber, scaleGrade, validateGrade };
