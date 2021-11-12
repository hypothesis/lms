import {
  APIError,
  formatErrorDetails,
  formatErrorMessage,
  isAuthorizationError,
  isLTILaunchServerError,
} from '../errors';

describe('APIError', () => {
  it('creates APIError with default properties', () => {
    const error = new APIError(404, {});

    assert.isUndefined(error.details);
    assert.isUndefined(error.errorCode);
    assert.equal(error.serverMessage, '');
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
    assert.equal(error.serverMessage, 'message');
    assert.equal(error.message, 'API call failed');
    assert.equal(error.status, 404);
  });
});

describe('isAuthorizationError', () => {
  [
    {
      error: new Error('This is any error'),
      expected: false,
    },
    {
      error: new APIError(404, { error_code: 'some-error-code' }),
      expected: false,
    },
    {
      error: new APIError(404, { message: 'Some message' }),
      expected: false,
    },
    {
      error: new APIError(404, {}),
      expected: true,
    },
    {
      error: new APIError(404, { details: 'moose' }),
      expected: true,
    },
  ].forEach((testCase, idx) => {
    it(`returns 'true' if provided error represents an authorization error (${idx})`, () => {
      assert.equal(isAuthorizationError(testCase.error), testCase.expected);
    });
  });
});

describe('isLTILaunchServerError', () => {
  [
    {
      error: new Error('any old error'),
      expected: false,
    },
    {
      error: new APIError(400, {}),
      expected: false,
    },
    {
      error: new APIError(400, { message: 'This is a server message' }),
      expected: false,
    },
    {
      error: new APIError(400, { error_code: 'rando-error-code' }),
      expected: false,
    },
    {
      error: new APIError(400, {
        error_code: 'blackboard_file_not_found_in_course',
      }),
      expected: true,
    },
  ].forEach(testCase => {
    it('should return `true` if the error has a recognized error code', () => {
      assert.equal(isLTILaunchServerError(testCase.error), testCase.expected);
    });
  });
});

describe('formatErrorMessage', () => {
  [
    {
      error: new Error('This is any old error'),
      expected: 'This is any old error',
    },
    {
      error: new APIError(400, { message: 'This is a server error' }),
      expected: 'This is a server error',
    },
    {
      error: new APIError(400, {}),
      expected: '',
    },
    {
      error: new APIError(400, {}),
      prefix: 'Something went wrong',
      expected: 'Something went wrong',
    },
    {
      error: new APIError(404, { message: 'This is a server explanation' }),
      prefix: 'Something went wrong',
      expected: 'Something went wrong: This is a server explanation',
    },
    {
      error: new Error('Any old error'),
      prefix: 'Something went wrong',
      expected: 'Something went wrong: Any old error',
    },
  ].forEach((testCase, idx) => {
    it(`should format the error message (${idx})`, () => {
      assert.equal(
        formatErrorMessage(testCase.error, testCase.prefix),
        testCase.expected
      );
    });
  });
});

describe('formatErrorDetails', () => {
  [
    {
      error: { details: { foo: 'bar' } },
      expected: JSON.stringify({ foo: 'bar' }, null, /* indent */ 2),
    },
    {
      error: {},
      expected: '',
    },
    {
      error: new APIError(400, { details: 'Hiya' }),
      expected: 'Hiya',
    },
    {
      error: new APIError(400, { details: { foo: 'bar' } }),
      expected: JSON.stringify({ foo: 'bar' }, null, /* indent */ 2),
    },
    {
      error: { details: null },
      expected: '',
    },
    {
      error: { details: {} },
      expected: '{}',
    },
    {
      error: { details: new Error('foo') },
      expected: '{}',
    },
  ].forEach(testCase => {
    it('should format error details', () => {
      assert.equal(formatErrorDetails(testCase.error), testCase.expected);
    });
  });
});
