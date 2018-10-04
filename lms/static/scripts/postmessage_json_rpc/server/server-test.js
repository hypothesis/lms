import Server from './server';

describe('postmessage_json_rpc/server#Server', () => {
  // The window origin of the server.
  // postMessage messages must be sent to this origin in order for the server
  // to receive them.
  const serversOrigin = 'http://localhost:9876';

  let configEl;
  let server;
  let registeredMethod;
  let listener;
  let receiveMessage;

  beforeEach('inject the server config into the document', () => {
    configEl = document.createElement('script');
    configEl.setAttribute('type', 'application/json');
    configEl.classList.add('js-rpc-server-config');
    configEl.textContent = JSON.stringify({
      allowedOrigins: ['http://localhost:9876'],
    });
    document.body.appendChild(configEl);
  });

  afterEach('remove the server config from the document', () => {
    configEl.parentNode.removeChild(configEl);
  });

  beforeEach('set up the test server', () => {
    server = new Server();
    registeredMethod = sinon.stub().returns('test_result');
    server.register('registeredMethodName', registeredMethod);
  });

  afterEach('tear down the test server', () => {
    server.off();
  });

  beforeEach('listen for JSON-RPC responses', () => {
    receiveMessage = sinon.stub();

    listener = (event) => {
      // Only call `receiveMessage` if the event is a JSON-RPC response.
      // This is to avoid calling receiveMessage with postMessage requests sent
      // by the tests (intended for the server).
      if (event.data.jsonrpc === '2.0' && (event.data.result || event.data.error)) {
        receiveMessage(event);
      }
    };

    window.addEventListener('message', listener);
  });

  afterEach('tear down the JSON-RPC response listener', () => {
    window.removeEventListener('message', listener);
  });

  /**
   * Return a valid JSON-RPC-over-postMessage request.
   *
   * Suitable for passing as the `message` argument to
   * window.postMessage(message, serversOrigin) in order to make an RPC request
   * to the server.
   */
  function validRequest() {
    return {
      jsonrpc: '2.0',
      id: 'test_id',
      method: 'registeredMethodName',
    };
  }

  describe('when a valid request is sent', () => {
    it('calls the registered method', () => {
      window.postMessage(validRequest(), serversOrigin);

      return new Promise((resolve, reject) => {
        receiveMessage.callsFake(() => {
          assert.isTrue(registeredMethod.calledOnce);
          assert.isTrue(registeredMethod.calledWithExactly());
          resolve();
        });
        window.setTimeout(
          reject,
          1500,
          new Error("Server's response wasn'treceived"),
        );
      });
    });

    [null, 'test_id'].forEach((id) => {
      it('sends a response message', () => {
        const request = validRequest();
        request.id = id;

        window.postMessage(request, serversOrigin);

        return new Promise((resolve, reject) => {
          receiveMessage.callsFake((event) => {
            assert.equal(event.data.jsonrpc, '2.0');
            assert.equal(event.data.result, 'test_result');
            assert.equal(event.data.id, id);
            resolve();
          });
          window.setTimeout(
            reject,
            1500,
            new Error("Server's response wasn'treceived"),
          );
        });
      });
    });
  });

  describe('when an invalid request is sent', () => {
    it("doesn't respond to requests from origins that aren't allowed", () => {
      server._allowedOrigins = ['https://example.com'];
      window.postMessage(validRequest(), serversOrigin);

      return new Promise((resolve, reject) => {
        receiveMessage.callsFake(() => {
          reject(new Error('No response message should be sent'));
        });
        window.setTimeout(resolve, 1);
      });
    });

    it("doesn't respond if request data isn't an object", () => {
      window.postMessage('not_an_object', serversOrigin);

      return new Promise((resolve, reject) => {
        receiveMessage.callsFake(() => {
          reject(new Error('No response message should be sent'));
        });
        window.setTimeout(resolve, 1);
      });
    });

    it("doesn't respond if the protocol spec is missing", () => {
      const request = validRequest();
      delete request.jsonrpc;

      window.postMessage(request, serversOrigin);

      return new Promise((resolve, reject) => {
        receiveMessage.callsFake(() => {
          reject(new Error('No response message should be sent'));
        });
        window.setTimeout(resolve, 1);
      });
    });

    it("doesn't respond if the protocol spec is wrong", () => {
      const request = validRequest();
      request.jsonrpc = '1.0';

      window.postMessage(request, serversOrigin);

      return new Promise((resolve, reject) => {
        receiveMessage.callsFake(() => {
          reject(new Error('No response message should be sent'));
        });
        window.setTimeout(resolve, 1);
      });
    });

    it("responds with an error if there's no request identifier", () => {
      const request = validRequest();
      delete request.id;

      window.postMessage(request, serversOrigin);

      return new Promise((resolve, reject) => {
        receiveMessage.callsFake((event) => {
          assert.equal(event.data.jsonrpc, '2.0');
          assert.equal(event.data.id, null);
          assert.equal(event.data.result, undefined);
          assert.equal(
            JSON.stringify(event.data.error),
            JSON.stringify({
              code: -32600,
              message: 'request id invalid',
            }),
          );
          resolve();
        });

        window.setTimeout(
          reject,
          1500,
          new Error("Server's response wasn't received"),
        );
      });
    });

    // The JSON-RPC spec says that `id` must be a number, string, or null.
    // If some other type of value is used the server should ignore the request.
    [{}, true, undefined].forEach((value) => {
      it('responds with an error if the request identifier is invalid', () => {
        const request = validRequest();
        request.id = value;

        window.postMessage(request, serversOrigin);

        return new Promise((resolve, reject) => {
          receiveMessage.callsFake((event) => {
            assert.equal(event.data.jsonrpc, '2.0');
            assert.equal(event.data.id, null);
            assert.equal(event.data.result, undefined);
            assert.equal(
              JSON.stringify(event.data.error),
              JSON.stringify({
                code: -32600,
                message: 'request id invalid',
              }),
            );
            resolve();
          });

          window.setTimeout(
            reject,
            1500,
            new Error("Server's response wasn't received"),
          );
        });
      });
    });

    it('responds with an error if the method name is missing', () => {
      const request = validRequest();
      delete request.method;

      window.postMessage(request, serversOrigin);

      return new Promise((resolve, reject) => {
        receiveMessage.callsFake((event) => {
          assert.equal(event.data.jsonrpc, '2.0');
          assert.equal(event.data.id, 'test_id');
          assert.equal(event.data.result, undefined);
          assert.equal(
            JSON.stringify(event.data.error),
            JSON.stringify({
              code: -32600,
              message: 'method name not recognized',
            }),
          );
          resolve();
        });

        window.setTimeout(
          reject,
          1500,
          new Error("Server's response wasn't received"),
        );
      });
    });

    [{}, true, 2.0, null].forEach((method_name) => {
      it("responds with an error if the method name isn't a string", () => {
        const request = validRequest();
        request.method = method_name;

        window.postMessage(request, serversOrigin);

        return new Promise((resolve, reject) => {
          receiveMessage.callsFake((event) => {
            assert.equal(event.data.jsonrpc, '2.0');
            assert.equal(event.data.id, 'test_id');
            assert.equal(event.data.result, undefined);
            assert.equal(
              JSON.stringify(event.data.error),
              JSON.stringify({
                code: -32600,
                message: 'method name not recognized',
              }),
            );
            resolve();
          });

          window.setTimeout(
            reject,
            1500,
            new Error("Server's response wasn't received"),
          );
        });
      });
    });
  });
});
