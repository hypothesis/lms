/**
 * Result of parsing a grade value entered by the user.
 *
 * This is either a grade value or a validation error message.
 */
export type ValidateGradeResult =
  | { valid: false; error: string }
  | { valid: true; grade: number };

/**
 * Validate a grade value entered by the user and convert it to a value which
 * can be submitted to the LMS.
 *
 * @param value - Grade value entered by the instructor
 * @param maxScore - Maximum numeric score that can be entered
 * @param scaleFactor - Amount to scale the input value by to get the grade
 *   value submitted to the LMS. This defaults to `1 / maxScore` so that the
 *   result is between 0 and 1, which is the range of grade values supported
 *   by LTI 1.1.
 * @return Validated grade value or validation error message.
 */
export function validateGrade(
  value: string,
  maxScore: number,
  scaleFactor: number = 1 / maxScore
): ValidateGradeResult {
  const trimmed = value.trim();

  // nb. If trimmed input is empty, `doubleVal` will be 0.
  const doubleVal = Number(trimmed);
  if (trimmed.length === 0 || isNaN(doubleVal)) {
    return {
      valid: false,
      error: `Grade must be a number between 0 and ${maxScore}`,
    };
  }

  if (doubleVal < 0 || doubleVal > maxScore) {
    return {
      valid: false,
      error: `Grade must be between 0 and ${maxScore}`,
    };
  }

  return { valid: true, grade: doubleVal * scaleFactor };
}

/**
 * Format a grade value received from the backend for display in the UI.
 *
 * LTI 1.1 represents grades as values in the range `[0, 1]`. These are scaled
 * in the UI to a score out of 10.
 *
 * @param grade - The saved grade value or `null` if no grade has been stored
 *   for the user.
 * @param scaleFactor - Amount to scale the value from the LMS to get the
 *   grade value that the user sees.
 */
export function formatGrade(grade: number | null, scaleFactor: number): string {
  if (grade === null) {
    return '';
  }

  let formatted = (grade * scaleFactor).toFixed(2);

  // Strip trailing zeros after decimal point.
  while (formatted.endsWith('0')) {
    formatted = formatted.slice(0, -1);
  }

  return formatted.replace(/\.$/, '');
}
