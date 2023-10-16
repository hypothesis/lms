import { formatGrade } from '../grade-validation';

const MAX_POINTS = 10;

describe('formatGrade', () => {
  [
    // No grade set
    [null, ''],

    // Cases where value formats as an integer
    [0, '0'],
    [0.3, '3'],
    [0.3001, '3'],
    [0.5, '5'],
    [0.9995, '10'],
    [1.0, '10'],

    // Cases where value formats as a float. We preserve up to 2dp.
    [0.33, '3.3'],
    [0.33333, '3.33'],
    [0.9994, '9.99'],
  ].forEach(([value, expected]) => {
    it('formats the grade as a value between 0 and 10', () => {
      assert.equal(formatGrade(value, MAX_POINTS), expected);
    });
  });
});
