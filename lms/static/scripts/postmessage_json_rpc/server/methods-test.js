import { requestConfig } from './methods';

describe('postmessage_json_rpc/methods#requestConfig', () => {
  let configEl;

  beforeEach('inject the client config into the document', () => {
    configEl = document.createElement('script');
    configEl.setAttribute('type', 'application/json');
    configEl.classList.add('js-hypothesis-config');
    configEl.textContent = JSON.stringify({foo: 'bar'});
    document.body.appendChild(configEl);
  });

  afterEach('remove the client config from the document', () => {
    configEl.parentNode.removeChild(configEl);
  });

  it('returns the config object', () => {
    assert.deepEqual(requestConfig(), {foo: 'bar'});
  });
});
