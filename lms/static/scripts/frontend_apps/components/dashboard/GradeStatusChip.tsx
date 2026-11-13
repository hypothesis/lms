import classnames from 'classnames';

export type GradeStatusChipProps = {
  /**
   * A grade, from 0 to 1, that will be used to render the corresponding
   * color combination.
   */
  grade: number;

  /** Render the grade in grey, whatever it is. */
  muted?: boolean;
};

/**
 * A grade from 0 to 1 as the percentage this app works in, rounded to the two
 * decimals it is displayed with.
 */
export function gradePercentage(grade: number): number {
  return Math.round(grade * 10000) / 100;
}

/**
 * Format a grade from 0 to 1 to a string. If the grade is an integer, it
 * will be returned as an integer string. Otherwise, it will be returned
 * with two decimal places.
 */
export function formatGrade(grade: number): string {
  const scaledGrade = gradePercentage(grade);

  return Number.isInteger(scaledGrade)
    ? scaledGrade.toString()
    : scaledGrade.toFixed(2);
}

/**
 * A badge where the corresponding color combination is calculated from a grade
 * from 0 to 1, following the next table:
 *
 *  1        - bright green
 *  0.8-0.99 - light green
 *  0.5-0.79 - yellow
 *  0.1-0.49 - light red
 *  0        - bright red
 *  other    - grey
 *
 * A muted chip is grey at any grade, for one which is not the grade of record.
 */
export default function GradeStatusChip({
  grade,
  muted = false,
}: GradeStatusChipProps) {
  const percentage = gradePercentage(grade);
  const gradeIsInvalid = percentage < 0 || percentage > 100;
  const isGrey = muted || gradeIsInvalid;

  return (
    <div
      className={classnames(
        'rounded inline-block font-bold px-2 py-0.5 cursor-default',
        {
          'bg-green-dark text-white': !isGrey && percentage === 100,
          'bg-green-light text-green-dark':
            !isGrey && percentage >= 80 && percentage < 100,
          'bg-yellow-light text-yellow-dark':
            !isGrey && percentage >= 50 && percentage < 80,
          'bg-red-light text-red-dark':
            !isGrey && percentage > 0 && percentage < 50,
          'bg-red-dark text-white': !isGrey && percentage === 0,
          'bg-grey-3 text-grey-7': isGrey,
        },
      )}
    >
      {formatGrade(grade)}
      {!gradeIsInvalid && '%'}
    </div>
  );
}
