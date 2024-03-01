import { render } from 'preact';

import { Config, readConfig, useConfig } from '../config';

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

  it('should throw if the .js-config object is missing', () => {
    configEl.remove();
    assert.throws(() => {
      readConfig();
    }, 'No config object found for selector ".js-config"');
  });

  it('should throw if the config cannot be parsed', () => {
    configEl.textContent = 'not valid JSON';
    assert.throws(() => {
      readConfig();
    }, 'Failed to parse frontend configuration');
  });

  it('should return the parsed configuration', () => {
    const config = readConfig();
    assert.deepEqual(config, expectedConfig);
  });
});

describe('useConfig', () => {
  const config = {
    someApp: { setting: true },
  };

  it('should return current config', () => {
    let result;
    function Widget() {
      result = useConfig();
    }

    render(
      <Config.Provider value={config}>
        <Widget />
      </Config.Provider>,
      document.createElement('div'),
    );

    assert.deepEqual(result, config);
  });

  it('should throw if required keys are not set', () => {
    function Widget() {
      useConfig(['otherApp']);
    }

    assert.throws(() => {
      render(
        <Config.Provider value={config}>
          <Widget />
        </Config.Provider>,
        document.createElement('div'),
      );
    }, 'Required configuration key "otherApp" not set');
  });
});
