import classnames from 'classnames';

export type GradeStatusChipProps = {
  /**
   * A grade, from 0 to 1, that will be used to render the corresponding
   * color combination.
   */
  grade: number;
};

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
 */
export default function GradeStatusChip({ grade }: GradeStatusChipProps) {
  const gradeIsInvalid = grade < 0 || grade > 1;

  return (
    <div
      className={classnames(
        'rounded inline-block font-bold px-2 py-0.5 cursor-default',
        {
          'bg-green-dark text-white': grade === 1,
          'bg-green-light text-green-dark': grade >= 0.8 && grade < 1,
          'bg-yellow-light text-yellow-dark': grade >= 0.5 && grade < 0.8,
          'bg-red-light text-red-dark': grade > 0 && grade < 0.5,
          'bg-red-dark text-white': grade === 0,
          'bg-grey-3 text-grey-7': gradeIsInvalid,
        },
      )}
    >
      {grade * 100}
      {!gradeIsInvalid && '%'}
    </div>
  );
}
