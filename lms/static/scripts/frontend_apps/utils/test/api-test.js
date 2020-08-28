import { ApiError, apiCall } from '../api';

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
      });
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
});
