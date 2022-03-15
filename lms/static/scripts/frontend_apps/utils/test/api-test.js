import { APIError } from '../../errors';
import { apiCall } from '../api';

function createResponse(status, body) {
  return {
    status,
    json: sinon.stub().resolves(body),
  };
}

describe('api', () => {
  let fakeResponse;

  beforeEach(() => {
    fakeResponse = createResponse(200, {
      id: 123,
      display_name: 'foo',
      updated_at: '2019-01-01',
    });
    sinon.stub(window, 'fetch').resolves(fakeResponse);

    window.fetch
      .withArgs('/api/canvas/refresh')
      .resolves(createResponse(200, null));
  });

  afterEach(() => {
    window.fetch.restore();
  });

  function getFetchPaths() {
    return window.fetch.args.map(fetchArgs => fetchArgs[0]);
  }

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

    it('sets query params if `params` is passed', async () => {
      const params = {
        a_key: 'some value',
        encode_me: 'https://example.com',
      };

      await apiCall({ path: '/api/test', authToken: 'auth', params });

      assert.calledWith(
        window.fetch,
        `/api/test?a_key=some+value&encode_me=${encodeURIComponent(
          params.encode_me
        )}`,
        {
          method: 'GET',
          body: undefined,
          headers: {
            Authorization: 'auth',
          },
        }
      );
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
        expectedMessage: '',
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
      it('throws an `APIError` if the request fails', async () => {
        fakeResponse.status = status;
        fakeResponse.json.resolves(body);

        const response = apiCall({ path: '/api/test', authToken: 'auth' });
        let reason;
        try {
          await response;
        } catch (err) {
          reason = err;
        }

        assert.instanceOf(reason, APIError);
        assert.equal(reason.message, 'API call failed', '`Error.message`');
        assert.equal(
          reason.serverMessage,
          expectedMessage,
          '`APIError.serverMessage`'
        );
        assert.equal(reason.details, body.details, '`APIError.details`');
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

  it('refreshes access tokens for external APIs', async () => {
    const refreshNeededResponse = createResponse(400, {
      refresh: { method: 'POST', path: '/api/canvas/refresh' },
    });
    window.fetch
      .withArgs('/api/test')
      .onFirstCall()
      .resolves(refreshNeededResponse);

    const result = await apiCall({ path: '/api/test', authToken: 'auth' });

    // Expect initial request, followed by token refresh, followed by a retry
    // of the original request.
    assert.deepEqual(getFetchPaths(), [
      '/api/test',
      '/api/canvas/refresh',
      '/api/test',
    ]);

    const refreshCall = window.fetch.secondCall;
    assert.deepEqual(refreshCall.args[1], {
      method: 'POST',
      body: undefined,
      headers: { Authorization: 'auth' },
    });

    assert.deepEqual(result, await fakeResponse.json());
  });

  it('only attempts a token refresh once per call', async () => {
    const refreshNeededResponse = createResponse(400, {
      refresh: { method: 'POST', path: '/api/canvas/refresh' },
    });

    // Make both the initial request and the request after the successful refresh
    // fail.
    window.fetch.resolves(refreshNeededResponse);

    let error;
    try {
      await apiCall({ path: '/api/test', authToken: 'auth' });
    } catch (e) {
      error = e;
    }

    assert.instanceOf(error, APIError);
    assert.equal(error.message, 'API call failed');
    assert.equal(error.status, 400);
  });

  it('rethrows token refresh failures', async () => {
    const refreshNeededResponse = createResponse(400, {
      refresh: { method: 'POST', path: '/api/canvas/refresh' },
    });
    window.fetch.resolves(refreshNeededResponse);
    window.fetch.withArgs('/api/canvas/refresh').resolves(
      createResponse(400, {
        message: 'Token refresh failed',
      })
    );

    let error;
    try {
      await apiCall({ path: '/api/test', authToken: 'auth' });
    } catch (e) {
      error = e;
    }

    assert.deepEqual(getFetchPaths(), ['/api/test', '/api/canvas/refresh']);
    assert.ok(error);
    assert.equal(error.message, 'API call failed');
    assert.equal(error.serverMessage, 'Token refresh failed');
  });

  it('prevents concurrent access token refreshes', async () => {
    const refreshNeededResponse = createResponse(400, {
      refresh: { method: 'POST', path: '/api/canvas/refresh' },
    });
    window.fetch
      .withArgs('/api/test')
      .onCall(0)
      .resolves(refreshNeededResponse);
    window.fetch
      .withArgs('/api/test')
      .onCall(1)
      .resolves(refreshNeededResponse);

    const firstCallPromise = apiCall({ path: '/api/test', authToken: 'auth' });
    const secondCallPromise = apiCall({ path: '/api/test', authToken: 'auth' });

    const [firstCallResult, secondCallResult] = await Promise.all([
      firstCallPromise,
      secondCallPromise,
    ]);

    // Expect two calls to `/api/test` that will fail due to a needed refresh,
    // followed by a refresh, followed by two retries of the original requests.
    assert.deepEqual(getFetchPaths(), [
      '/api/test',
      '/api/test',
      '/api/canvas/refresh',
      '/api/test',
      '/api/test',
    ]);

    assert.deepEqual(firstCallResult, await fakeResponse.json());
    assert.deepEqual(secondCallResult, await fakeResponse.json());
  });
});
