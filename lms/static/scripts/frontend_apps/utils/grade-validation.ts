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
