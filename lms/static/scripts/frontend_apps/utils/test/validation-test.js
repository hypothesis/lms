import { formatToNumber, scaleGrade, validateGrade } from '../validation';

describe('#validation', () => {
  describe('formatToNumber', () => {
    it('translates the string to a number', () => {
      assert.isTrue(formatToNumber('1') === 1);
    });

    it('does not translate the empty string to a number', () => {
      assert.isTrue(typeof formatToNumber(' ') === 'string');
    });

    it('does not translate a non numerical string to a number', () => {
      assert.isTrue(typeof formatToNumber('a') === 'string');
    });

    it('translates the string to a number with leading and trailing spaces', () => {
      assert.isTrue(formatToNumber(' 1 ') === 1);
    });
  });

  describe('#validateGrade', () => {
    it('fails validation if the value is not a number', () => {
      assert.equal(validateGrade('1'), 'Grade must be a valid number');
    });

    it('fails validation if the value is less than 0', () => {
      assert.equal(validateGrade(-1), 'Grade must be between 0 and 10');
    });

    it('fails validation if the value is greater than 10', () => {
      assert.equal(validateGrade(11), 'Grade must be between 0 and 10');
    });

    it('passes validation if its a valid number between 0 and 10', () => {
      assert.equal(validateGrade(1), undefined);
    });
  });

  describe('#scaleGrade', () => {
    const GRADE_MULTIPLIER = 10;
    it('scales the grade by 10', () => {
      assert.strictEqual(scaleGrade(0.5, GRADE_MULTIPLIER), '5');
    });
    it('does not lose precision', () => {
      // note: 0.33 * 10 = 3.3000000000000003
      assert.strictEqual(scaleGrade(0.33, GRADE_MULTIPLIER), '3.3');
    });
    it('rounds to same number of significant figures', () => {
      assert.strictEqual(scaleGrade(0.9999, GRADE_MULTIPLIER), '9.999');
    });
    it('returns a string when input is 0', () => {
      assert.strictEqual(scaleGrade(0, GRADE_MULTIPLIER), '0');
    });
    it('returns a string when input is 1', () => {
      assert.strictEqual(scaleGrade(1, GRADE_MULTIPLIER), '10');
    });
    it('does not care about trailing zeros', () => {
      assert.strictEqual(scaleGrade(0.9, GRADE_MULTIPLIER), '9');
    });
  });
});
