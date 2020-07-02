import { readConfig } from '../config';

describe('readConfig', () => {
  let expectedConfig;
  let configEl;

  beforeEach(() => {
    expectedConfig = {
      allowedOrigins: ['https://hypothes.is'],
    };
    configEl = document.createElement('script');
    configEl.className = 'js-config';
    configEl.type = 'application/json';
    configEl.textContent = JSON.stringify(expectedConfig);
    document.body.appendChild(configEl);
  });

  afterEach(() => {
    configEl.remove();
  });

  it('should throw an error if the .js-config object is missing', () => {
    configEl.remove();
    assert.throws(() => {
      readConfig();
    }, 'No config object found for selector ".js-config"');
  });

  it('should return the parsed configuration', () => {
    const config = readConfig();
    assert.deepEqual(config, expectedConfig);
  });
});
