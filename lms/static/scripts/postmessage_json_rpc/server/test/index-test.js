import { startRpcServer, getSidebarWindow, $imports } from '../index';

describe('postmessage_json_rpc/server', () => {
  let FakeServer;
  let FakeRegister;

  beforeEach(() => {
    FakeRegister = sinon.stub();

    FakeServer = sinon.stub().returns({
      register: FakeRegister,
      sidebarWindow: 'FakeSidebarWindow',
    });

    $imports.$mock({
      './server': FakeServer,
    });
  });

  afterEach('remove the server config from the document', () => {
    $imports.$restore();
  });

  describe('#startRpcServer', () => {
    it('returns a server object', async () => {
      const server = startRpcServer();
      assert.isTrue(FakeServer.called);
      assert.isOk(server);
    });
  });

  describe('#getSidebarWindow', () => {
    it('returns the value of server.sidebarWindow', async () => {
      startRpcServer();
      assert.equal(getSidebarWindow(), 'FakeSidebarWindow');
    });
  });

  describe('registered methods', () => {
    describe('requestGroups', () => {
      it('returns the groups through the resolveGroupFetch promise resolver', async () => {
        const server = startRpcServer();
        server.resolveGroupFetch(['group1', 'group2']); // exposed resolver
        assert.match(
          await FakeRegister.withArgs(
            'requestGroups',
            sinon.match.func
          ).args[0][1](),
          ['group1', 'group2']
        );
      });
    });

    describe('requestConfig', () => {
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

      it('returns the .js-config json object', async () => {
        startRpcServer();
        assert.match(
          FakeRegister.withArgs('requestConfig', sinon.match.func).args[0][1](),
          { foo: 'bar' }
        );
      });
    });
  });
});
