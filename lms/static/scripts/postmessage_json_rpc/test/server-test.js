import { delay } from '@hypothesis/frontend-testing';

import { Server } from '../server';

describe('Server', () => {
  /**
   * Return a Promise that simply resolves itself after a given delay.
   */
  function resolveAfterDelay() {
    return new Promise(resolve => {
      window.setTimeout(resolve, 1);
    });
  }

  /**
   * Return a Promise that simply rejects after a given delay.
   */
  function rejectAfterDelay(message) {
    return new Promise((resolve, reject) => {
      window.setTimeout(reject, 1500, new Error(message));
    });
  }

  /**
   * Return a valid JSON-RPC-over-postMessage request.
   *
   * Suitable for passing as the `message` argument to
   * window.postMessage(message, serversOrigin) in order to make an RPC request
   * to the server.
   */
  function validRequest(method = 'registeredMethodName') {
    return {
      jsonrpc: '2.0',
      id: 'test_id',
      method,
    };
  }

  function validNotificationRequest(method = 'registeredMethodName') {
    return {
      jsonrpc: '2.0',
      method,
    };
  }

  // The window origin of the server.
  // postMessage messages must be sent to this origin in order for the server
  // to receive them.
  let serversOrigin;

  let server;
  let registeredMethod;
  let registeredMethodError;
  let listener;
  let receiveMessage;

  beforeEach('set up the test server', () => {
    // The test server normally runs on http://localhost:9876, but may be
    // on a higher port if multiple instances are running.
    // Use window.location.origin to be safe.
    serversOrigin = window.location.origin;
    server = new Server([serversOrigin]);
    registeredMethod = sinon.stub().resolves('test_result');
    server.register('registeredMethodName', registeredMethod);

    registeredMethodError = sinon
      .stub()
      .rejects(new Error('method threw an error'));
    server.register('registeredMethodErrorName', registeredMethodError);
  });

  afterEach('tear down the test server', () => {
    server.off();
  });

  beforeEach('listen for JSON-RPC responses', () => {
    receiveMessage = sinon.stub();

    listener = event => {
      // Only call `receiveMessage` if the event is a JSON-RPC response.
      // This is to avoid calling receiveMessage with postMessage requests sent
      // by the tests (intended for the server).
      if (
        event.data.jsonrpc === '2.0' &&
        (event.data.result || event.data.error)
      ) {
        receiveMessage(event);
      }
    };

    window.addEventListener('message', listener);
  });

  afterEach('tear down the JSON-RPC response listener', () => {
    window.removeEventListener('message', listener);
  });

  describe('when a valid request is sent', () => {
    it('calls the registered method', () => {
      window.postMessage(validRequest(), serversOrigin);

      return Promise.race([
        new Promise(resolve => {
          receiveMessage.callsFake(() => {
            assert.isTrue(registeredMethod.calledOnce);
            assert.isTrue(registeredMethod.calledWithExactly());
            resolve();
          });
        }),
        rejectAfterDelay("Server's response wasn't received"),
      ]);
    });

    it('calls the registered method with the provided params', () => {
      const request = validRequest();
      request.params = ['foo', 5];
      window.postMessage(request, serversOrigin);

      return Promise.race([
        new Promise(resolve => {
          receiveMessage.callsFake(() => {
            assert.calledWith(registeredMethod, 'foo', 5);
            resolve();
          });
        }),
        rejectAfterDelay("Server's response wasn't received"),
      ]);
    });

    it('calls the registered method that throws an error', () => {
      window.postMessage(
        validRequest('registeredMethodErrorName'),
        serversOrigin,
      );
      return Promise.race([
        new Promise(resolve => {
          receiveMessage.callsFake(() => {
            assert.isTrue(registeredMethodError.calledOnce);
            assert.isTrue(registeredMethodError.calledWithExactly());
            resolve();
          });
        }),
        rejectAfterDelay("Server's response wasn't received"),
      ]);
    });

    [null, 'test_id'].forEach(id => {
      it('sends a response message', () => {
        const request = validRequest();
        request.id = id;

        window.postMessage(request, serversOrigin);

        return Promise.race([
          new Promise(resolve => {
            receiveMessage.callsFake(event => {
              assert.equal(event.data.jsonrpc, '2.0');
              assert.equal(event.data.result, 'test_result');
              assert.equal(event.data.id, id);
              resolve();
            });
          }),
          rejectAfterDelay("Server's response wasn't received"),
        ]);
      });
    });
  });

  describe('when a valid notification request is received', () => {
    beforeEach(() => {
      const errorMethod = sinon.stub().throws();
      server.register('errorMethod', errorMethod);
      sinon.stub(console, 'error');
    });

    afterEach(() => {
      console.error.restore();
    });

    it('calls the registered method', async () => {
      window.postMessage(validNotificationRequest(), serversOrigin);
      await delay(0);
      assert.calledOnce(registeredMethod);
    });

    it('calls the registered method with the provided params', async () => {
      const request = validNotificationRequest();
      request.params = ['foo', 5];
      window.postMessage(request, serversOrigin);
      await delay(0);
      assert.calledWith(registeredMethod, 'foo', 5);
    });

    it('logs thrown error from the registered method', async () => {
      window.postMessage(
        validNotificationRequest('errorMethod'),
        serversOrigin,
      );

      await delay(0);

      assert.calledOnce(console.error);
      assert.include(
        console.error.getCall(0).args[0],
        'JSON-RPC notification method failed:',
      );
    });
  });

  describe('when an invalid notification request is received', () => {
    beforeEach(() => {
      sinon.stub(console, 'error');
    });

    afterEach(() => {
      console.error.restore();
    });

    it('logs if method name unrecognized', async () => {
      window.postMessage(
        validNotificationRequest('randoMethod'),
        serversOrigin,
      );

      await delay(0);

      assert.calledOnce(console.error);
      assert.include(
        console.error.getCall(0).args[0],
        'Received JSON-RPC notification for unrecognized method: randoMethod',
      );
    });
  });

  describe('when an invalid request is sent', () => {
    it("doesn't respond to requests from origins that aren't allowed", () => {
      server._allowedOrigins = ['https://example.com'];
      window.postMessage(validRequest(), serversOrigin);

      return assertThatTheServerDidntRespond();
    });

    it("doesn't respond if request data isn't an object", () => {
      window.postMessage('not_an_object', serversOrigin);

      return assertThatTheServerDidntRespond();
    });

    it("doesn't respond if the protocol spec is missing", () => {
      const request = validRequest();
      delete request.jsonrpc;

      window.postMessage(request, serversOrigin);

      return assertThatTheServerDidntRespond();
    });

    it("doesn't respond if the protocol spec is wrong", () => {
      const request = validRequest();
      request.jsonrpc = '1.0';

      window.postMessage(request, serversOrigin);

      return assertThatTheServerDidntRespond();
    });

    // The JSON-RPC spec says that `id` must be a number, string, or null if
    // it is present. If it is not present, the request is assumed to be
    // a notification.
    [{}, true].forEach(value => {
      it('responds with an error if the request identifier is invalid', () => {
        const request = validRequest();
        request.id = value;

        window.postMessage(request, serversOrigin);

        return assertThatServerRespondedWithError('request id invalid', null);
      });
    });

    it('responds with an error if the method name is missing', () => {
      const request = validRequest();
      delete request.method;

      window.postMessage(request, serversOrigin);

      return assertThatServerRespondedWithError('method name not recognized');
    });

    [{}, true, 2.0, null].forEach(method_name => {
      it("responds with an error if the method name isn't a string", () => {
        const request = validRequest();
        request.method = method_name;

        window.postMessage(request, serversOrigin);

        return assertThatServerRespondedWithError('method name not recognized');
      });
    });
  });

  /**
   * Return a Promise that rejects if a response from the server is received.
   * Resolves otherwise.
   */
  function assertThatTheServerDidntRespond() {
    return Promise.race([
      new Promise((resolve, reject) => {
        receiveMessage.callsFake(() => {
          reject(new Error('No response message should be sent'));
        });
      }),
      resolveAfterDelay(),
    ]);
  }

  /**
   * Return a Promise that resolves if the server responds with a given error.
   * Rejects otherwise.
   */
  function assertThatServerRespondedWithError(message, id = 'test_id') {
    return Promise.race([
      new Promise(resolve => {
        receiveMessage.callsFake(event => {
          assert.equal(event.data.jsonrpc, '2.0');
          assert.equal(event.data.id, id);
          assert.equal(event.data.result, undefined);
          assert.deepEqual(event.data.error, {
            code: -32600,
            message: message,
          });
          resolve();
        });
      }),
      rejectAfterDelay("Server's response wasn't received"),
    ]);
  }
});
