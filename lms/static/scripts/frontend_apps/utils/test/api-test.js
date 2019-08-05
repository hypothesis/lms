import { ApiError, apiCall, listFiles } from '../api';

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
        },
      });
    });

    it("returns the response's JSON content", async () => {
      const result = await apiCall({ path: '/api/test', authToken: 'auth' });
      assert.deepEqual(result, await fakeResponse.json());
    });
  });

  describe('listFiles', () => {
    it('fetches file data from the backend', async () => {
      const response = listFiles('auth-token', 'course-id');
      assert.calledWith(window.fetch, '/api/canvas/courses/course-id/files', {
        method: 'GET',
        body: undefined,
        headers: {
          Authorization: 'auth-token',
        },
      });
      const data = await response;
      assert.deepEqual(data, await fakeResponse.json());
    });
  });

  context('when an API call fails', () => {
    [
      {
        status: 403,
        body: { error_message: null, details: {} },
        expectedMessage: 'API call failed',
      },
      {
        status: 400,
        body: { error_message: 'Something went wrong', details: {} },
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

        const response = listFiles('auth-token', 'course-id');
        let reason;
        try {
          await response;
        } catch (err) {
          reason = err;
        }

        assert.instanceOf(reason, ApiError);
        assert.equal(reason.message, expectedMessage);
        assert.equal(reason.errorMessage, body.error_message);
        assert.equal(reason.details, body.details);
      });
    });
  });

  it('throws original error if `fetch` or parsing JSON fails', async () => {
    fakeResponse.json.rejects(new TypeError('Parse failed'));

    const response = listFiles('auth-token', 'course-id');
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
