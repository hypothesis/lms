/**
 * Methods that're remotely callable by JSON-RPC over postMessage.
 *
 * Methods that can be remotely called by clients using our
 * JSON-RPC-over-postMessage server (postmessage_json_rpc/server/server.js) are
 * defined in one place in this module.
 */

/**
 * Return a Hypothesis client config object for the current LTI request.
 */
export function requestConfig() {
  const configEl = document.querySelector('.js-config');
  const clientConfigObj = JSON.parse(configEl.textContent).hypothesisClient;
  return clientConfigObj;
}

/**
 * The client sends this request when it's ready to receive incoming RPC
 * requests.
 */
export function readyToReceive() {
  // TOOD: resolve promise to unblock any outgoing rpc
  // requests that were waiting.
  // e.g. server._resolveSidebarWindow
  return {};
}
