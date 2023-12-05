import { init, $imports } from '../index';

// Minimal version of the configuration that the backend renders into the page.
const minimalConfig = {
  api: {
    authToken: '1234',
  },
  hypothesisClient: {},
  rpcServer: {
    allowedOrigins: ['https://example.com'],
  },
  mode: 'basic-lti-launch',
};

describe('LMS frontend entry', () => {
  let AppRoot;
  let container;
  let fakeContentInfoFetcher;
  let fakeReadConfig;

  beforeEach(() => {
    container = document.createElement('div');
    container.id = 'app';
    document.body.append(container);

    fakeContentInfoFetcher = {
      fetch: sinon.stub(),
    };
    fakeReadConfig = sinon.stub().returns(minimalConfig);

    // eslint-disable-next-line prefer-arrow-callback
    AppRoot = sinon.spy(function AppRoot() {
      return <div data-testid="app-root" />;
    });

    $imports.$mock({
      './components/AppRoot': AppRoot,
      './config': { readConfig: fakeReadConfig },
      './services': {
        ClientRPC: sinon.stub(),
        ContentInfoFetcher: sinon.stub().returns(fakeContentInfoFetcher),
        GradingService: sinon.stub(),
        VitalSourceService: sinon.stub(),
      },
    });
  });

  afterEach(() => {
    container.remove();
    $imports.$restore();
  });

  ['basic-lti-launch', 'email-notifications'].forEach(mode => {
    it('renders root component', () => {
      fakeReadConfig.returns({ ...minimalConfig, mode });

      init();

      const container = document.querySelector('#app');
      assert.ok(container.querySelector('[data-testid=app-root]'));

      assert.called(AppRoot);
      const props = AppRoot.args[0][0];
      assert.equal(props.initialConfig, fakeReadConfig());
      assert.instanceOf(props.services, Map);
    });
  });

  it('console logs debug values', () => {
    const log = sinon.stub(console, 'log');

    try {
      fakeReadConfig.returns({
        ...minimalConfig,
        debug: { values: { key: 'value' } },
      });

      init();

      assert.calledWith(log, 'key: value');
    } finally {
      log.restore();
    }
  });

  describe('LTI launch', () => {
    it('fetches data for content banner, if configured', () => {
      const contentBanner = { source: 'jstor', itemId: '12345' };
      fakeReadConfig.returns({ ...minimalConfig, contentBanner });

      init();

      assert.calledWith(fakeContentInfoFetcher.fetch, contentBanner);
    });
  });
});
