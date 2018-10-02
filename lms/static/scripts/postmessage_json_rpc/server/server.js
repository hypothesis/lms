

export default class Server {

  constructor(config) {
    // JSON-RPC messages that don't come from one of these allow window origins
    // will be ignored.
    this._allowedOrigins = config.allowedOrigins;

    // Add a postMessage event listener so we can recieve JSON-RPC requests.
    this._boundReceiveMessage = this._receiveMessage.bind(this);
    window.addEventListener('message', this._boundReceiveMessage);

    // The methods that can be called remotely via this server.
    this._registeredMethods = {};
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
  _receiveMessage(event) {
    if (!this._allowedOrigins.includes(event.origin)) {
      return;
    }

    if (!this._isJSONRPCRequest(event)) {
      return;
    }

    event.source.postMessage(this._jsonRPCResponse(event.data), event.origin);
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
  _jsonRPCResponse(request) {
    // Return an error response if the request id is invalid.
    // id must be a string, number or null.
    const id = event.data.id;
    if (!(['string', 'number'].includes(typeof id) || id === null)) {
      return {
        jsonrpc: '2.0',
        id: null,
        error: {code: -32600, message: 'request id invalid'},
      };
    }

    const method = this._registeredMethods[request.method];

    // Return an error response if the method name is invalid.
    if (method === undefined) {
      return {
        jsonrpc: '2.0',
        id: request.id,
        error: {code: -32600, message: 'method name not recognized'},
      };
    }

    // Call the method and return the result response.
    return {jsonrpc: '2.0', result: method(), id: request.id};
  }
}
