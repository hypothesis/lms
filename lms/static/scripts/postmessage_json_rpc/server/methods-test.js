import { requestConfig, requestFrame } from './methods';

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

  it('returns the config object', async () => {
    const result = await requestConfig();
    assert.deepEqual(result, { foo: 'bar' });
  });

  it('returns the parameters passed to requestFrame', async () => {
    const result = await requestFrame({ bar: 1 });
    assert.deepEqual(result, { bar: 1 });
  });
});
