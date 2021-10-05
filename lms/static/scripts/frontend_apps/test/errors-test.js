import { APIError } from '../errors';

describe('APIError', () => {
  it('creates APIError with default properties', () => {
    const error = new APIError(404, {});

    assert.isUndefined(error.details);
    assert.isNull(error.errorCode);
    assert.isNull(error.errorMessage);
    assert.equal(error.message, 'API call failed');
    assert.equal(error.status, 404);
  });

  it('creates `APIError` with optional properties', () => {
    const details = { myDetails: 'p' };
    const error = new APIError(404, {
      message: 'message',
      error_code: '4xx',
      details,
      ignored: 'dummy',
    });

    assert.equal(error.details, details);
    assert.equal(error.errorCode, '4xx');
    assert.equal(error.errorMessage, 'message');
    assert.equal(error.message, 'message');
    assert.equal(error.status, 404);
  });
});
