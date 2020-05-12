import { startRpcServer, getSidebarWindow, $imports } from '../index';

describe('postmessage_json_rpc/server/index', () => {
  let FakeServer;
  let fakeRegister;

  beforeEach(() => {
    fakeRegister = sinon.stub();

    FakeServer = sinon.stub().returns({
      register: fakeRegister,
      sidebarWindow: 'FakeSidebarWindow',
    });

    $imports.$mock({
      './server': FakeServer,
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  describe('startRpcServer', () => {
    it('returns a server object', () => {
      const server = startRpcServer();
      assert.isTrue(FakeServer.called);
      assert.isOk(server);
    });
  });

  describe('getSidebarWindow', () => {
    it('returns the value of server.sidebarWindow', () => {
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
          await fakeRegister
            .withArgs('requestGroups', sinon.match.func)
            .args[0][1](),
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
        configEl.remove();
      });

      it('returns the .js-config json object', () => {
        startRpcServer();
        assert.match(
          fakeRegister.withArgs('requestConfig', sinon.match.func).args[0][1](),
          { foo: 'bar' }
        );
      });
    });
  });
});
