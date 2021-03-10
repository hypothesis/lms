import { $imports, ClientRpc } from '../client-rpc';

describe('ClientRpc', () => {
  let authToken;
  let clientConfig;
  let fakeApiCall;

  let FakeServer;
  let fakeServerInstance;

  let fakeSidebarWindow;
  let fakeRpcCall;

  let FakeJWT;
  let fakeJwt;

  beforeEach(() => {
    clientConfig = {
      showHighlights: true,
      services: [
        {
          grantToken: 'initial.grant.token',
        },
      ],
    };

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

    FakeJWT = sinon.spy(token => {
      fakeJwt = {
        hasExpired: sinon.stub().returns(false),
        value: () => token,
      };
      return fakeJwt;
    });

    let grantTokenCounter = 0;
    fakeApiCall = sinon.spy(async () => {
      ++grantTokenCounter;
      return {
        grant_token: 'new.grant.token-' + grantTokenCounter,
      };
    });

    authToken = 'dummy-auth-token';

    $imports.$mock({
      '../utils/api': {
        apiCall: fakeApiCall,
      },
      '../utils/jwt': {
        JWT: FakeJWT,
      },
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
      authToken,
      clientConfig,
    });
  }

  it('initializes RPC server that accepts requests from specified origins', () => {
    createClientRpc();
    assert.calledWith(FakeServer, ['https://client.hypothes.is']);
  });

  describe('"requestConfig" RPC handler', () => {
    it('is registered', () => {
      createClientRpc();
      assert.calledWith(fakeServerInstance.register, 'requestConfig');
    });

    it('returns client config', async () => {
      createClientRpc();
      const [, callback] = fakeServerInstance.register.args.find(
        ([method]) => method === 'requestConfig'
      );
      assert.equal(await callback(), clientConfig);
    });

    it('returns initial grant token if still valid', async () => {
      createClientRpc();

      const [, callback] = fakeServerInstance.register.args.find(
        ([method]) => method === 'requestConfig'
      );
      const config = await callback();

      assert.notCalled(fakeApiCall);
      assert.calledWith(FakeJWT, 'initial.grant.token', sinon.match.number);
      assert.equal(config.services[0].grantToken, 'initial.grant.token');
    });

    it('fetches and returns new grant token if it has expired', async () => {
      createClientRpc();
      const [, callback] = fakeServerInstance.register.args.find(
        ([method]) => method === 'requestConfig'
      );

      // Simulate initial grant token expiring. This should trigger fetching of
      // a new token.
      fakeJwt.hasExpired.returns(true);
      let config = await callback();
      assert.calledWith(fakeApiCall, {
        authToken,
        path: '/api/grant_token',
      });
      assert.equal(config.services[0].grantToken, 'new.grant.token-1');

      // Re-fetch config before the new token expires.
      fakeApiCall.resetHistory();
      fakeJwt.hasExpired.returns(false);

      config = await callback();

      assert.notCalled(fakeApiCall);
      assert.equal(config.services[0].grantToken, 'new.grant.token-1');

      // Re-fetch config after the new token expires.
      fakeJwt.hasExpired.returns(true);

      config = await callback();

      assert.calledWith(fakeApiCall, { authToken, path: '/api/grant_token' });
      assert.equal(config.services[0].grantToken, 'new.grant.token-2');
    });
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
