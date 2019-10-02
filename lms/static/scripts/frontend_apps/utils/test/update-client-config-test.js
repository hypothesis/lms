import {
  updateClientConfig,
  removeClientConfig,
} from '../update-client-config';

describe('update-client-config', () => {
  let fakeHypothesisConfig;
  let fakeScriptNode;

  beforeEach(() => {
    fakeHypothesisConfig = sinon.stub(document, 'querySelector');
    fakeScriptNode = {
      text: JSON.stringify({}), // empty default value
    };
    fakeHypothesisConfig
      .withArgs('.js-hypothesis-config')
      .returns(fakeScriptNode);
  });

  afterEach(() => {
    fakeHypothesisConfig.restore();
  });

  it('sets the config', async () => {
    updateClientConfig({ test: true });
    sinon.assert.match(JSON.parse(fakeScriptNode.text), { test: true });
  });

  it('removes specified keys from the config', async () => {
    updateClientConfig({ test: true, foo: true, bar: true });
    removeClientConfig(['foo', 'bar']);
    sinon.assert.match(JSON.parse(fakeScriptNode.text), { test: true });
  });

  it('multiple calls to do not override previous state', async () => {
    updateClientConfig({ test1: true });
    updateClientConfig({ test2: true });
    sinon.assert.match(JSON.parse(fakeScriptNode.text), {
      test1: true,
      test2: true,
    });
  });
});
