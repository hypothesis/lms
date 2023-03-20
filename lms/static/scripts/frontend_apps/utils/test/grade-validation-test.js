import { formatGrade, validateGrade } from '../grade-validation';

const MAX_POINTS = 10;

describe('validateGrade', () => {
  [
    // Valid grade values
    ['0', 0],
    ['10', 1],
    ['3', 3 / 10],
    ['5', 5 / 10],
    ['5.5', 55 / 100],

    // Leading and trailing spaces
    [' 1 ', 1 / 10],
  ].forEach(([input, expected]) => {
    it('returns parsed grade if valid', () => {
      const result = validateGrade(input, MAX_POINTS);
      assert.isTrue(result.ok);
      assert.approximately(result.grade, expected, 1e-8 /* tolerance */);
    });
  });

  [
    ['', 'Grade must be a number between 0 and 10'],
    ['foo', 'Grade must be a number between 0 and 10'],
    ['2b', 'Grade must be a number between 0 and 10'],
    ['-1', 'Grade must be between 0 and 10'],
    ['20', 'Grade must be between 0 and 10'],
  ].forEach(([input, error]) => {
    it('returns error if validation fails', () => {
      assert.deepEqual(validateGrade(input, MAX_POINTS), { ok: false, error });
    });
  });
});

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
