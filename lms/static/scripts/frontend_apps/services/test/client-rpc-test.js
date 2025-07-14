import sinon from 'sinon';

import { $imports, ClientRPC } from '../client-rpc';

describe('ClientRPC', () => {
  let authToken;
  let clientConfig;
  let fakeApiCall;

  let FakeServer;
  let fakeServerInstance;

  let fakeSidebarWindow;
  let fakeRpcCall;

  let FakeJWT;
  let fakeJwt;

  let fakeIncrementUnsavedCount;
  let fakeDecrementUnsavedCount;

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
    fakeApiCall = sinon.stub().callsFake(async () => {
      ++grantTokenCounter;
      return {
        grant_token: 'new.grant.token-' + grantTokenCounter,
      };
    });

    authToken = 'dummy-auth-token';

    fakeIncrementUnsavedCount = sinon.stub();
    fakeDecrementUnsavedCount = sinon.stub();

    $imports.$mock({
      '../utils/api': {
        apiCall: fakeApiCall,
      },
      '../utils/jwt': {
        JWT: FakeJWT,
      },
      '../utils/unsaved-changes': {
        incrementUnsavedCount: fakeIncrementUnsavedCount,
        decrementUnsavedCount: fakeDecrementUnsavedCount,
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

  function createClientRPC() {
    return new ClientRPC({
      allowedOrigins: ['https://client.hypothes.is'],
      authToken,
      clientConfig,
    });
  }

  it('initializes RPC server that accepts requests from specified origins', () => {
    createClientRPC();
    assert.calledWith(FakeServer, ['https://client.hypothes.is']);
  });

  describe('"requestConfig" RPC handler', () => {
    it('is registered', () => {
      createClientRPC();
      assert.calledWith(fakeServerInstance.register, 'requestConfig');
    });

    it('returns client config', async () => {
      createClientRPC();
      const [, callback] = fakeServerInstance.register.args.find(
        ([method]) => method === 'requestConfig',
      );
      assert.equal(await callback(), clientConfig);
    });

    it('returns initial grant token if still valid', async () => {
      createClientRPC();

      const [, callback] = fakeServerInstance.register.args.find(
        ([method]) => method === 'requestConfig',
      );
      const config = await callback();

      assert.notCalled(fakeApiCall);
      assert.calledWith(FakeJWT, 'initial.grant.token', sinon.match.number);
      assert.equal(config.services[0].grantToken, 'initial.grant.token');
    });

    it('fetches and returns new grant token if it has expired', async () => {
      createClientRPC();
      const [, callback] = fakeServerInstance.register.args.find(
        ([method]) => method === 'requestConfig',
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

    it('reports error to client if grant token fetch fails', async () => {
      createClientRPC();
      const [, callback] = fakeServerInstance.register.args.find(
        ([method]) => method === 'requestConfig',
      );

      fakeJwt.hasExpired.returns(true);
      fakeApiCall.rejects(new Error('Something went wrong'));

      try {
        await callback();
      } catch (err) {
        assert.equal(
          err.message,
          'Unable to fetch Hypothesis login. Please reload the assignment.',
        );
      }
    });
  });

  describe('"requestAuthToken" RPC handler', () => {
    it('returns auth token', async () => {
      createClientRPC();

      const [, callback] = fakeServerInstance.register.args.find(
        ([method]) => method === 'requestAuthToken',
      );
      const returnedAuthToken = await callback();

      assert.equal(authToken, returnedAuthToken);
    });
  });

  describe('reportActivity', () => {
    it('calls registered callback with annotation activity parameters', () => {
      const clientRPC = createClientRPC();
      const callback = sinon.stub();
      const [, serverMethod] = fakeServerInstance.register.args.find(
        ([method]) => method === 'reportActivity',
      );
      clientRPC.on('annotationActivity', callback);

      serverMethod('create', 'foo');

      assert.calledWith(callback, 'create', 'foo');
    });
  });

  it('registers "requestGroups" RPC handler', () => {
    createClientRPC();
    assert.calledWith(fakeServerInstance.register, 'requestGroups');
  });

  describe('setGroups', () => {
    it('sets the groups returned by "requestGroups" RPC handler', async () => {
      const clientRPC = createClientRPC();
      clientRPC.setGroups(['groupA', 'groupB']);

      const [, callback] = fakeServerInstance.register.args.find(
        ([method]) => method === 'requestGroups',
      );
      const groups = await callback();

      assert.deepEqual(groups, ['groupA', 'groupB']);
    });
  });

  describe('setFocusedUser', () => {
    it('sets focused user in client when user is passed', async () => {
      const clientRPC = createClientRPC();
      const studentGroups = [{ groupid: '1' }, { groupid: '2' }];

      await clientRPC.setFocusedUser(
        {
          userid: 'acct:123@lms.hypothes.is',
          displayName: 'Student A',
        },
        studentGroups,
      );

      assert.calledWith(
        fakeRpcCall,
        fakeSidebarWindow.frame,
        fakeSidebarWindow.origin,
        'changeFocusModeUser',
        [
          {
            username: 'acct:123@lms.hypothes.is',
            displayName: 'Student A',
            groups: studentGroups,
          },
        ],
      );
    });

    it('clears focused user in client when user is `null`', async () => {
      const clientRPC = createClientRPC();

      await clientRPC.setFocusedUser(null);

      assert.calledWith(
        fakeRpcCall,
        fakeSidebarWindow.frame,
        fakeSidebarWindow.origin,
        'changeFocusModeUser',
        [
          {
            username: undefined,
            displayName: undefined,
            groups: undefined,
          },
        ],
      );
    });
  });

  describe('showContentInfo', () => {
    it('sends content banner data to client', async () => {
      const contentInfo = { item: { title: 'Test article' } };
      const clientRPC = createClientRPC();

      await clientRPC.showContentInfo(contentInfo);

      assert.calledWith(
        fakeRpcCall,
        fakeSidebarWindow.frame,
        fakeSidebarWindow.origin,
        'showContentInfo',
        [contentInfo],
      );
    });
  });

  describe('"reportUnsavedChanges" RPC handler', () => {
    it('is registered', () => {
      createClientRPC();
      assert.calledWith(fakeServerInstance.register, 'reportUnsavedChanges');
    });

    it('calls incrementUnsavedCount when unsaved changes are reported', () => {
      createClientRPC();
      const [, callback] = fakeServerInstance.register.args.find(
        ([method]) => method === 'reportUnsavedChanges',
      );

      callback({ unsaved: true });

      assert.calledOnce(fakeIncrementUnsavedCount);
      assert.notCalled(fakeDecrementUnsavedCount);
    });

    it('calls decrementUnsavedCount when unsaved changes are cleared', () => {
      createClientRPC();
      const [, callback] = fakeServerInstance.register.args.find(
        ([method]) => method === 'reportUnsavedChanges',
      );

      // First set to true to establish state
      callback({ unsaved: true });
      fakeIncrementUnsavedCount.resetHistory();
      fakeDecrementUnsavedCount.resetHistory();

      // Then set to false to clear unsaved changes
      callback({ unsaved: false });

      assert.calledOnce(fakeDecrementUnsavedCount);
      assert.notCalled(fakeIncrementUnsavedCount);
    });

    it('does not increment or decrement unsaved count when state has not changed', () => {
      createClientRPC();
      const [, callback] = fakeServerInstance.register.args.find(
        ([method]) => method === 'reportUnsavedChanges',
      );

      // First call with unsaved: true
      callback({ unsaved: true });
      assert.calledOnce(fakeIncrementUnsavedCount);
      fakeIncrementUnsavedCount.resetHistory();

      // Second call with same state
      callback({ unsaved: true });
      assert.notCalled(fakeIncrementUnsavedCount);
      assert.notCalled(fakeDecrementUnsavedCount);
    });
  });
});
