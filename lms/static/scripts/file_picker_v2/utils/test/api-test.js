import { AuthorizationError, listFiles } from '../api';

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

  describe('listFiles', () => {
    it('fetches file data from the backend', async () => {
      const response = listFiles('auth-token', 'course-id');
      assert.calledWith(window.fetch, '/api/canvas/courses/course-id/files', {
        headers: {
          Authorization: 'auth-token',
        },
      });
      const data = await response;
      assert.deepEqual(data, await fakeResponse.json());
    });

    it('throws an `AuthorizationError` if authorization fails', async () => {
      fakeResponse.status = 403;
      const response = listFiles('auth-token', 'course-id');
      let reason;
      try {
        await response;
      } catch (err) {
        reason = err;
      }
      assert.instanceOf(reason, AuthorizationError);
    });
  });
});
