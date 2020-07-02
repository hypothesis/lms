import { startRpcServer, getSidebarWindow, $imports } from '../index';

describe('postmessage_json_rpc/server/index', () => {
  let FakeServer;
  let fakeRegister;
  let config;

  beforeEach(() => {
    fakeRegister = sinon.stub();

    FakeServer = sinon.stub().returns({
      register: fakeRegister,
      sidebarWindow: 'FakeSidebarWindow',
    });

    config = {
      allowedOrigins: ['http://hypothes.is'],
      clientConfig: { aSetting: 'aValue' },
    };

    $imports.$mock({
      './server': FakeServer,
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  describe('startRpcServer', () => {
    it('returns a server object', () => {
      const server = startRpcServer(config);
      assert.isTrue(FakeServer.called);
      assert.isOk(server);
    });
  });

  describe('getSidebarWindow', () => {
    it('returns the value of server.sidebarWindow', () => {
      startRpcServer(config);
      assert.equal(getSidebarWindow(), 'FakeSidebarWindow');
    });
  });

  describe('registered methods', () => {
    describe('requestGroups', () => {
      it('returns the groups through the resolveGroupFetch promise resolver', async () => {
        const server = startRpcServer(config);
        server.resolveGroupFetch(['group1', 'group2']); // exposed resolver
        assert.match(
          await fakeRegister
            .withArgs('requestGroups', sinon.match.func)
            .args[0][1](),
          ['group1', 'group2']
        );
      });
    });

    describe('requestConfig', () => {
      it('returns the Hypothesis client configuration', () => {
        startRpcServer(config);
        assert.equal(
          fakeRegister.withArgs('requestConfig', sinon.match.func).args[0][1](),
          config.clientConfig
        );
      });
    });
  });
});
