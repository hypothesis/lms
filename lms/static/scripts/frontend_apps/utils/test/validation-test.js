import { translateToNumber, validateGrade } from '../validation';

describe('validation', () => {
  context('translateToNumber', () => {
    it('translates the string to a number', async () => {
      assert.isTrue(translateToNumber('1') === 1);
    });

    it('does not translate the empty string to a number', async () => {
      assert.isTrue(typeof translateToNumber(' ') === 'string');
    });

    it('does not translate a non numerical string to a number', async () => {
      assert.isTrue(typeof translateToNumber('a') === 'string');
    });
  });

  context('validateGrade', () => {
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
});
