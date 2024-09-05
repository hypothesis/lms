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
      className={classnames('rounded font-bold inline-block px-2 py-0.5', {
        // We would usually use our standard `green-success` and `red-error`
        // colors here, but they don't have enough contrast when used with
        // white text and a small font.
        // Instead, we use slightly darker shades of green and red.
        'bg-[#008558] text-white': grade === 100,
        'bg-[#D7373A] text-white': grade === 0,
        'bg-green-200 text-green-900': grade >= 80 && grade < 100,
        'bg-amber-100 text-amber-900': grade >= 50 && grade < 80,
        'bg-red-200 text-red-900': grade >= 1 && grade < 50,
        'bg-grey-3 text-grey-7': gradeIsInvalid,
      })}
    >
      {grade}
      {!gradeIsInvalid && '%'}
    </div>
  );
}
