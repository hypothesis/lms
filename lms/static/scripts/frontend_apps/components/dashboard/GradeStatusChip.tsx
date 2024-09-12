import classnames from 'classnames';

export type GradeStatusChipProps = {
  /**
   * A grade, from 0 to 100, that will be used to render the corresponding
   * color combination.
   */
  grade: number;
};

/**
 * A badge where the corresponding color combination is calculated from a grade
 * from 0 to 100, following the next table:
 *
 *  100   - bright green
 *  80-99 - light green
 *  50-79 - yellow
 *  1-49  - light red
 *  0     - bright red
 *  other - grey
 */
export default function GradeStatusChip({ grade }: GradeStatusChipProps) {
  const gradeIsInvalid = grade < 0 || grade > 100;

  return (
    <div
      className={classnames(
        'rounded inline-block font-bold px-2 py-0.5 cursor-default',
        {
          'bg-grade-success text-white': grade === 100,
          'bg-grade-success-light text-grade-success':
            grade >= 80 && grade < 100,
          'bg-grade-warning-light text-grade-warning':
            grade >= 50 && grade < 80,
          'bg-grade-error-light text-grade-error': grade >= 1 && grade < 50,
          'bg-grade-error text-white': grade === 0,
          'bg-grey-3 text-grey-7': gradeIsInvalid,
        },
      )}
    >
      {grade}
      {!gradeIsInvalid && '%'}
    </div>
  );
}
