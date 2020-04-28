import { requestConfig, requestGroups, $imports } from './methods';

describe('postmessage_json_rpc/methods#requestConfig', () => {
  let configEl;

  beforeEach('inject the client config into the document', () => {
    configEl = document.createElement('script');
    configEl.setAttribute('type', 'application/json');
    configEl.classList.add('js-config');
    configEl.textContent = JSON.stringify({
      hypothesisClient: { foo: 'bar' },
    });
    document.body.appendChild(configEl);
  });

  afterEach('remove the client config from the document', () => {
    configEl.parentNode.removeChild(configEl);
  });

  it('returns the config object', () => {
    assert.deepEqual(requestConfig(), { foo: 'bar' });
  });
});

describe('postmessage_json_rpc/methods#requestGroups', () => {
  let configEl;
  let fakeApiCall;

  beforeEach('inject the client config into the document', () => {
    fakeApiCall = sinon.stub();
    $imports.$mock({
      '../../frontend_apps/utils/api': {
        apiCall: fakeApiCall,
      },
    });

    configEl = document.createElement('script');
    configEl.setAttribute('type', 'application/json');
    configEl.classList.add('js-config');
    configEl.textContent = JSON.stringify({
      api: {
        authToken: 'dummyAuthToken',
        sync: {
          data: {
            course: {
              context_id: '12345',
              custom_canvas_course_id: '101',
            },
          },
          path: '/api/sync',
        },
      },
    });
    document.body.appendChild(configEl);
  });

  afterEach('remove the client config from the document', () => {
    configEl.parentNode.removeChild(configEl);
  });

  it('calls the remote endpoint specified in .js-config when `requestGroups` is called', async () => {
    await requestGroups();
    assert.calledWith(fakeApiCall, {
      authToken: 'dummyAuthToken',
      path: '/api/sync',
      data: {
        course: {
          context_id: '12345',
          custom_canvas_course_id: '101',
        },
      },
    });
  });
});
