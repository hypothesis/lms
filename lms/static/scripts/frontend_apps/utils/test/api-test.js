import { waitFor } from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

import { Config } from '../../config';
import { APIError } from '../../errors';
import {
  apiCall,
  urlPath,
  useAPIFetch,
  $imports,
  usePaginatedAPIFetch,
} from '../api';

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

      assert.calledWith(
        window.fetch,
        '/api/test',
        sinon.match({
          method: 'GET',
          headers: {
            Authorization: 'auth',
          },
        }),
      );
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
          params.encode_me,
        )}`,
        sinon.match({
          method: 'GET',
          headers: {
            Authorization: 'auth',
          },
        }),
      );
    });

    it('makes a POST request if a body is provided', async () => {
      const data = { param: 'value' };
      await apiCall({ path: '/api/test', authToken: 'auth', data });

      assert.calledWith(
        window.fetch,
        '/api/test',
        sinon.match({
          method: 'POST',
          body: JSON.stringify(data),
          headers: {
            Authorization: 'auth',
            'Content-Type': 'application/json; charset=UTF-8',
          },
        }),
      );
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
          '`APIError.serverMessage`',
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

    const controller = new AbortController();
    const result = await apiCall({
      path: '/api/test',
      authToken: 'auth',
      signal: controller.signal,
    });

    // Expect initial request, followed by token refresh, followed by a retry
    // of the original request.
    assert.deepEqual(getFetchPaths(), [
      '/api/test',
      '/api/canvas/refresh',
      '/api/test',
    ]);

    const refreshCall = window.fetch.secondCall;
    assert.match(refreshCall.args[1], {
      method: 'POST',
      body: undefined,
      headers: { Authorization: 'auth' },
      signal: controller.signal,
    });

    assert.deepEqual(result, await fakeResponse.json());

    // Though we didn't cancel the request at any point, check that the signal
    // was passed to each `fetch` call so that it would have been aborted if
    // needed.
    for (const call of window.fetch.getCalls()) {
      assert.equal(call.args[1].signal, controller.signal);
    }
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
      }),
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

  it('passes abort signal to fetch', async () => {
    const controller = new AbortController();
    window.fetch.rejects(new DOMException('Request canceled', 'AbortError'));

    const result = apiCall({
      path: '/api/test',
      authToken: 'auth',
      signal: controller.signal,
    });

    assert.calledWith(
      window.fetch,
      '/api/test',
      sinon.match({ method: 'GET', signal: controller.signal }),
    );

    // Simulate request being canceled, as `fetch` would do if we called
    // `controller.abort()`, and check that the AbortError is re-thrown.
    let error;
    try {
      await result;
    } catch (e) {
      error = e;
    }

    assert.instanceOf(error, Error);
    assert.equal(error.name, 'AbortError');
  });

  it('retries if an HTTP 409 response is received', async () => {
    const conflictResponse = createResponse(409, {});
    const okResponse = createResponse(200, { ok: true });

    window.fetch.withArgs('/api/test').onCall(0).resolves(conflictResponse);
    window.fetch.withArgs('/api/test').onCall(1).resolves(conflictResponse);
    window.fetch.withArgs('/api/test').onCall(2).resolves(okResponse);

    const retryDelay = 1;

    // An HTTP 409 response should trigger an automatic retry.
    const result = await apiCall({
      path: '/api/test',
      authToken: 'auth',
      retryDelay,
    });

    assert.deepEqual(result, { ok: true });

    // Automatic retries should stop after we hit the retry limit.
    window.fetch.resetHistory();
    let error;
    try {
      await apiCall({
        path: '/api/test',
        authToken: 'auth',
        maxRetries: 1,
        retryDelay,
      });
    } catch (err) {
      error = err;
    }

    assert.instanceOf(error, APIError);
    assert.equal(error.status, 409);
  });
});

describe('urlPath', () => {
  it('escapes path parameters', () => {
    const thingId = 'abc/123:456%789';
    const encodedThingId = encodeURIComponent(thingId);
    const subThingId = '<foo>';
    const encodedSubThingId = encodeURIComponent(subThingId);

    const path = urlPath`/api/things/${thingId}/sub-things/${subThingId}`;

    assert.equal(
      path,
      `/api/things/${encodedThingId}/sub-things/${encodedSubThingId}`,
    );
  });

  it('returns path with no parameters unchanged', () => {
    assert.equal(urlPath`/api/foo/bar`, '/api/foo/bar');
  });
});

describe('useAPIFetch', () => {
  let fakeConfig;
  let fakeUseFetch;
  let fakeFetchResult;

  beforeEach(() => {
    fakeConfig = {
      api: { authToken: 'some-token' },
    };
    fakeFetchResult = { data: {}, error: null, isLoading: false };
    fakeUseFetch = sinon.stub().returns(fakeFetchResult);

    const fakeUseConfig = sinon.stub();
    fakeUseConfig.returns(fakeConfig);

    $imports.$mock({
      '../config': { useConfig: fakeUseConfig },
      './fetch': { useFetch: fakeUseFetch },
    });

    sinon.stub(window, 'fetch').resolves(createResponse(200, {}));
  });

  afterEach(() => {
    $imports.$restore();
    window.fetch.restore();
  });

  [
    {
      path: '/api/some/path',
      params: undefined,
      expectedURL: '/api/some/path',
    },
    {
      path: '/api/some/path',
      params: {},
      expectedURL: '/api/some/path',
    },
    {
      path: '/api/some/path',
      params: { ignored: [] },
      expectedURL: '/api/some/path',
    },
    {
      path: '/api/some/path',
      params: { foo: 'bar', baz: 'meep' },
      expectedURL: '/api/some/path?foo=bar&baz=meep',
    },
    {
      path: '/api/some/path',
      params: { foo: 'bar', array: ['hello', 'world'] },
      expectedURL: '/api/some/path?foo=bar&array=hello&array=world',
    },
  ].forEach(({ path, params, expectedURL }) => {
    it('fetches data from API if a path is provided', async () => {
      const result = useAPIFetch(path, params);
      assert.equal(result, fakeFetchResult);
      assert.calledWith(fakeUseFetch, expectedURL, sinon.match.func);

      const fetcher = fakeUseFetch.args[0][1];
      const { signal } = new AbortController();
      await fetcher(signal);

      assert.calledWith(
        window.fetch,
        expectedURL,
        sinon.match({
          headers: {
            Authorization: fakeConfig.api.authToken,
          },
          signal,
        }),
      );
    });
  });

  it('does not fetch if no path is provided', () => {
    useAPIFetch(null);
    assert.calledWith(fakeUseFetch, null, undefined);
  });

  // Integration test with `useFetch` and Preact
  it('fetches data in a component', async () => {
    $imports.$restore();
    window.fetch
      .withArgs('/api/some/path')
      .resolves(createResponse(200, { title: 'Some title' }));

    function TestWidget() {
      const result = useAPIFetch('/api/some/path');
      return (
        <div>
          {result.isLoading && 'Loading'}
          {result.data && result.data.title}
          {result.error && `Error: ${result.error}`}
        </div>
      );
    }

    const wrapper = mount(
      <Config.Provider value={fakeConfig}>
        <TestWidget />
      </Config.Provider>,
    );
    assert.equal(wrapper.text(), 'Loading');

    await waitFor(() => wrapper.text() === 'Some title');
  });
});

describe('usePaginatedAPIFetch', () => {
  let fakeUseFetch;
  const pageResults = [
    {
      items: [1, 2, 3],
      next: 'page-2',
    },
    {
      items: [4, 5, 6],
      next: 'page-3',
    },
    {
      items: [7],
      next: null,
    },
  ];

  function mockFetchResult({ items, next }) {
    fakeUseFetch.returns({
      data: {
        items,
        pagination: { next },
      },
      isLoading: false,
    });
  }

  function mockLoadingState() {
    fakeUseFetch.returns({
      data: null,
      isLoading: true,
    });
  }

  beforeEach(() => {
    fakeUseFetch = sinon.stub();
    mockFetchResult(pageResults[0]);

    const fakeUseConfig = sinon.stub();
    fakeUseConfig.returns({
      api: { authToken: 'some-token' },
    });

    $imports.$mock({
      '../config': { useConfig: fakeUseConfig },
      './fetch': { useFetch: fakeUseFetch },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  function TestWidget({ params = {} }) {
    const result = usePaginatedAPIFetch('items', '/api/some/path', params);
    return (
      <div>
        <div data-testid="main-content">
          {result.isLoadingFirstPage
            ? 'Initial load'
            : result.isLoading && 'Loading'}
          {!result.isLoading &&
            (result.data ? result.data.join(',') : 'No content')}
        </div>

        <button
          onClick={() => result.loadNextPage()}
          data-testid="load-next-button"
        >
          Load next
        </button>
      </div>
    );
  }

  function createComponent() {
    return mount(<TestWidget />);
  }

  function loadNextPage(wrapper) {
    wrapper.find('[data-testid="load-next-button"]').simulate('click');
  }

  function getMainContent(wrapper) {
    return wrapper.find('[data-testid="main-content"]').text();
  }

  function reRender(wrapper) {
    // Setting the same props again will force the component to re-render
    wrapper.setProps(wrapper.props());
  }

  it('loads first page initially', () => {
    const wrapper = createComponent();
    assert.equal(getMainContent(wrapper), '1,2,3');
  });

  it('loads next pages when requested', () => {
    const wrapper = createComponent();
    assert.equal(getMainContent(wrapper), '1,2,3');

    // Click and load second page
    mockFetchResult(pageResults[1]);
    loadNextPage(wrapper);
    assert.equal(getMainContent(wrapper), '1,2,3,4,5,6');

    // Click and load third page
    mockFetchResult(pageResults[2]);
    loadNextPage(wrapper);
    assert.equal(getMainContent(wrapper), '1,2,3,4,5,6,7');

    // After third page, no more results will be appended
    loadNextPage(wrapper);
    assert.equal(getMainContent(wrapper), '1,2,3,4,5,6,7');
  });

  it('is initially loading when no data is set yet', () => {
    mockLoadingState();

    const wrapper = createComponent();
    assert.equal(getMainContent(wrapper), 'Initial load');
  });

  it('is loading when further pages are loaded after first one', () => {
    // Load first page by default
    const wrapper = createComponent();
    assert.equal(getMainContent(wrapper), '1,2,3');

    // When loading again, we no longer consider it's the first load
    mockLoadingState();
    reRender(wrapper);
    assert.equal(getMainContent(wrapper), 'Loading');
  });

  it('resets to first page when params change', () => {
    // Load first page by default
    const wrapper = createComponent();
    assert.equal(getMainContent(wrapper), '1,2,3');

    // Click and load second page
    mockFetchResult(pageResults[1]);
    loadNextPage(wrapper);
    assert.equal(getMainContent(wrapper), '1,2,3,4,5,6');

    // After updating params, content should be reset
    wrapper.setProps({
      params: { foo: 'bar' },
    });
    assert.equal(getMainContent(wrapper), 'No content');
  });
});
