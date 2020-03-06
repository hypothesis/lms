/**
 * A JSON-RPC-over-postMessage server.
 *
 * On creation the server automatically finds and reads its config settings
 * from a JSON config object in the document. For example:
 *
 *     <script type="application/json" class="js-config">
 *       {
 *         rpcServer: { allowedOrigins: ["https://hypothes.is"] }
 *       }
 *     </script>
 *
 * After constructing a server you have to call its register() method to
 * register remotely callable methods. After a method has been registered the
 * server will respond to remote requests for that method by caling the method
 * and sending the method's return value, serialized to a JSON string, back to
 * the caller over postMessage. For example:
 *
 *     const server = new Server();
 *     server.register('requestConfig', requestConfig);
 *
 */
export default class Server {
  constructor() {
    const configEl = document.getElementsByClassName('js-config')[0];
    const configObj = JSON.parse(configEl.textContent).rpcServer;

    // JSON-RPC messages that don't come from one of these allowed window
    // origins will be ignored.
    this._allowedOrigins = configObj.allowedOrigins;

    // Add a postMessage event listener so we can recieve JSON-RPC requests.
    this._boundReceiveMessage = this._receiveMessage.bind(this);
    window.addEventListener('message', this._boundReceiveMessage);

    // The methods that can be called remotely via this server.
    this._registeredMethods = {};

    this.sidebarWindow = new Promise(resolve => {
      this._resolveSidebarWindow = resolve;
    });
  }

  /**
   * Register a remotely callable method with this server.
   */
  register(name, method) {
    this._registeredMethods[name] = method;
  }

  /**
   * Turn off this Server instance, it will no longer respond to messages.
   */
  off() {
    window.removeEventListener('message', this._boundReceiveMessage);
  }

  /**
   * Receive a JSON-RPC-postMessage request and respond to it.
   *
   * Receive a postMessage event and, if it's a JSON-RPC request from an
   * allowed origin, post back either a result or an error response.
   */
  async _receiveMessage(event) {
    if (!this._allowedOrigins.includes(event.origin)) {
      return;
    }

    if (!this._isJSONRPCRequest(event)) {
      return;
    }
    // Resolve the promise we created in the constructor with the saved
    // sidebar frame and origin.
    this._resolveSidebarWindow({
      frame: event.source,
      origin: event.origin,
    });

    const result = await this._jsonRPCResponse(event.data);
    event.source.postMessage(result, event.origin);
  }

  /**
   * Return true if the given postMessage event is a JSON-RPC request.
   */
  _isJSONRPCRequest(event) {
    if (!(event.data instanceof Object) || event.data.jsonrpc !== '2.0') {
      // Event is neither a JSON-RPC request or response.
      return false;
    }

    if (event.data.result || event.data.error) {
      // Event is a JSON-RPC _response_, rather than a request.
      return false;
    }

    return true;
  }

  /**
   * Return a JSON-RPC response object for the given JSON-RPC request object.
   */
  async _jsonRPCResponse(request) {
    // Return an error response if the request id is invalid.
    // id must be a string, number or null.
    const id = request.id;
    if (!(['string', 'number'].includes(typeof id) || id === null)) {
      return {
        jsonrpc: '2.0',
        id: null,
        error: { code: -32600, message: 'request id invalid' },
      };
    }

    const method = this._registeredMethods[request.method];

    // Return an error response if the method name is invalid.
    if (method === undefined) {
      return {
        jsonrpc: '2.0',
        id: request.id,
        error: { code: -32600, message: 'method name not recognized' },
      };
    }

    // Call the method and return the result response.
    try {
      const result = await method();
      return { jsonrpc: '2.0', result: result, id: request.id };
    } catch (e) {
      return {
        jsonrpc: '2.0',
        id: request.id,
        error: { code: -32600, message: e.message },
      };
    }
  }
}
