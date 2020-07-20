import { $imports, ClientRpc } from '../client-rpc';

describe('ClientRpc', () => {
  let clientConfig;
  let FakeServer;
  let fakeSidebarWindow;
  let fakeRpcCall;
  let fakeServerInstance;

  beforeEach(() => {
    clientConfig = { showHighlights: true };

    fakeSidebarWindow = {
      frame: {},
      origin: 'https://client.hypothes.is',
    };

    fakeServerInstance = {
      register: sinon.stub(),
      sidebarWindow: fakeSidebarWindow,
    };

    fakeRpcCall = sinon.stub();

    FakeServer = sinon.stub().returns(fakeServerInstance);

    $imports.$mock({
      '../../postmessage_json_rpc': {
        Server: FakeServer,
        call: fakeRpcCall,
      },
    });
  });

  afterEach(() => {
    $imports.$restore();
  });

  function createClientRpc() {
    return new ClientRpc({
      allowedOrigins: ['https://client.hypothes.is'],
      clientConfig,
    });
  }

  it('initializes RPC server that accepts requests from specified origins', () => {
    createClientRpc();
    assert.calledWith(FakeServer, ['https://client.hypothes.is']);
  });

  it('registers "requestConfig" RPC handler that returns client config', () => {
    createClientRpc();
    assert.calledWith(fakeServerInstance.register, 'requestConfig');
    const [, callback] = fakeServerInstance.register.args.find(
      ([method]) => method === 'requestConfig'
    );
    assert.equal(callback(), clientConfig);
  });

  it('registers "requestGroups" RPC handler', () => {
    createClientRpc();
    assert.calledWith(fakeServerInstance.register, 'requestGroups');
  });

  describe('setGroups', () => {
    it('sets the groups returned by "requestGroups" RPC handler', async () => {
      const clientRpc = createClientRpc();
      clientRpc.setGroups(['groupA', 'groupB']);

      const [, callback] = fakeServerInstance.register.args.find(
        ([method]) => method === 'requestGroups'
      );
      const groups = await callback();

      assert.deepEqual(groups, ['groupA', 'groupB']);
    });
  });

  describe('setFocusedUser', () => {
    it('sets focused user in client when user is passed', async () => {
      const clientRpc = createClientRpc();

      await clientRpc.setFocusedUser({
        userid: 'acct:123@lms.hypothes.is',
        displayName: 'Student A',
      });

      assert.calledWith(
        fakeRpcCall,
        fakeSidebarWindow.frame,
        fakeSidebarWindow.origin,
        'changeFocusModeUser',
        [
          {
            username: 'acct:123@lms.hypothes.is',
            displayName: 'Student A',
          },
        ]
      );
    });

    it('clears focused user in client when user is `null`', async () => {
      const clientRpc = createClientRpc();

      await clientRpc.setFocusedUser(null);

      assert.calledWith(
        fakeRpcCall,
        fakeSidebarWindow.frame,
        fakeSidebarWindow.origin,
        'changeFocusModeUser',
        [
          {
            username: undefined,
            displayName: undefined,
          },
        ]
      );
    });
  });
});
