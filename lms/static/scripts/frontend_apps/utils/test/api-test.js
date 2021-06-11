import { ApiError, apiCall, fetchBooks, fetchChapters } from '../api';

describe('api', () => {
  let fakeResponse;

  beforeEach(() => {
    fakeResponse = {
      status: 200,
      json: sinon
        .stub()
        .resolves([{ id: 123, display_name: 'foo', updated_at: '2019-01-01' }]),
    };
    sinon.stub(window, 'fetch').resolves(fakeResponse);
  });

  afterEach(() => {
    window.fetch.restore();
  });

  describe('apiCall', () => {
    it('makes a GET request if no body is provided', async () => {
      await apiCall({ path: '/api/test', authToken: 'auth' });

      assert.calledWith(window.fetch, '/api/test', {
        method: 'GET',
        body: undefined,
        headers: {
          Authorization: 'auth',
        },
      });
    });

    it('makes a POST request if a body is provided', async () => {
      const data = { param: 'value' };
      await apiCall({ path: '/api/test', authToken: 'auth', data });

      assert.calledWith(window.fetch, '/api/test', {
        method: 'POST',
        body: JSON.stringify(data),
        headers: {
          Authorization: 'auth',
          'Content-Type': 'application/json; charset=UTF-8',
        },
      });
    });

    it("returns the response's JSON content", async () => {
      const result = await apiCall({ path: '/api/test', authToken: 'auth' });
      assert.deepEqual(result, await fakeResponse.json());
    });
  });

  context('when an API call fails', () => {
    [
      {
        status: 403,
        body: { message: null, details: {} },
        expectedMessage: 'API call failed',
      },
      {
        status: 400,
        body: { message: 'Something went wrong', details: {} },
        expectedMessage: 'Something went wrong',
      },
      {
        status: 404,
        body: { message: 'Unknown endpoint' },
        expectedMessage: 'Unknown endpoint',
      },
    ].forEach(({ status, body, expectedMessage }) => {
      it('throws an `ApiError` if the request fails', async () => {
        fakeResponse.status = status;
        fakeResponse.json.resolves(body);

        const response = apiCall({ path: '/api/test', authToken: 'auth' });
        let reason;
        try {
          await response;
        } catch (err) {
          reason = err;
        }

        assert.instanceOf(reason, ApiError);
        assert.equal(reason.message, expectedMessage, '`Error.message`');
        assert.equal(
          reason.errorMessage,
          body.message,
          '`ApiError.errorMessage`'
        );
        assert.equal(reason.details, body.details, '`ApiError.details`');
        assert.equal(reason.errorCode, null);
      });
    });

    it('sets `errorCode` property if server provides an `error_code`', async () => {
      fakeResponse.status = 400;
      fakeResponse.json.resolves({
        error_code: 'canvas_api_permission_error',
        details: {},
      });

      const response = apiCall({ path: '/api/test', authToken: 'auth' });
      let reason;
      try {
        await response;
      } catch (err) {
        reason = err;
      }

      assert.equal(reason.errorCode, 'canvas_api_permission_error');
    });
  });

  it('throws original error if `fetch` or parsing JSON fails', async () => {
    fakeResponse.json.rejects(new TypeError('Parse failed'));

    const response = apiCall({ path: '/api/test', authToken: 'auth' });
    let reason;
    try {
      await response;
    } catch (err) {
      reason = err;
    }

    assert.instanceOf(reason, TypeError);
    assert.equal(reason.message, 'Parse failed');
  });

  describe('fetchBooks', () => {
    it('returns book data', async () => {
      const data = await fetchBooks('auth-token', 1 /* delay */);
      assert.isTrue(Array.isArray(data));
      assert.equal(data.length, 2);
    });
  });

  describe('fetchChapters', () => {
    it('returns chapter list', async () => {
      const data = await fetchChapters(
        'auth-token',
        'BOOKSHELF-TUTORIAL',
        1 /* delay */
      );
      assert.isTrue(Array.isArray(data));
      assert.equal(data.length, 45);
    });

    it('throws if book ID is unknown', async () => {
      let err;
      try {
        await fetchChapters('auth-token', 'unknown-book-id', 1 /* delay */);
      } catch (e) {
        err = e;
      }
      assert.instanceOf(err, ApiError);
      assert.equal(err.message, 'Book not found');
    });
  });
});
