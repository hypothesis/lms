import { formatToNumber, scaleGrade, validateGrade } from '../validation';

describe('#validation', () => {
  describe('formatToNumber', () => {
    it('translates the string to a number', async () => {
      assert.isTrue(formatToNumber('1') === 1);
    });

    it('does not translate the empty string to a number', async () => {
      assert.isTrue(typeof formatToNumber(' ') === 'string');
    });

    it('does not translate a non numerical string to a number', async () => {
      assert.isTrue(typeof formatToNumber('a') === 'string');
    });

    it('translates the string to a number with leading and trailing spaces', async () => {
      assert.isTrue(formatToNumber(' 1 ') === 1);
    });
  });

  describe('#validateGrade', () => {
    it('fails validation if the value is not a number', async () => {
      assert.equal(validateGrade('1'), 'Grade must be a valid number');
    });

    it('fails validation if the value is less than 0', async () => {
      assert.equal(validateGrade(-1), 'Grade must be between 0 and 10');
    });

    it('fails validation if the value is greater than 10', async () => {
      assert.equal(validateGrade(11), 'Grade must be between 0 and 10');
    });

    it('passes validation if its a valid number between 0 and 10', async () => {
      assert.equal(validateGrade(1), undefined);
    });
  });

  describe('#scaleGrade', () => {
    const GRADE_MULTIPLIER = 10;
    it('scales the grade by 10', async () => {
      assert.equal(scaleGrade(0.5, GRADE_MULTIPLIER), 5);
    });
    it('does not lose precision', async () => {
      // note: 0.33 * 10 = 3.3000000000000003
      assert.equal(scaleGrade(0.33, GRADE_MULTIPLIER), 3.3);
    });
    it('rounds to same number of significate figures', async () => {
      assert.equal(scaleGrade(0.9999, GRADE_MULTIPLIER), 9.999);
    });
    it('does not scale 0', async () => {
      assert.equal(scaleGrade(0, GRADE_MULTIPLIER), 0);
    });
    it('does not care about trailing zeros', async () => {
      assert.equal(scaleGrade(0.9, GRADE_MULTIPLIER), 9);
    });
  });
});
