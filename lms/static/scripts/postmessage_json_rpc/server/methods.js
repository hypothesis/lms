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
export async function requestConfig() {
  const configEl = document.querySelector('.js-config');
  const clientConfigObj = JSON.parse(configEl.textContent).hypothesisClient;
  return Promise.resolve(clientConfigObj);
}

/**
 * Method that is used to trace back to the sender which frame
 * is the embedding ancestor frame. An acknowledgment of this
 * request tells the sender that this frame is the controlling
 * embedder frame.
 *
 * @param {Object} params - Parameter object to round trip. Use this
 *  to store a unique index when performing discovery.
 * @return {Promise<Object>} Successful promise returning the
 *  passed in parameter object.
 */
export async function requestFrame(params) {
  return Promise.resolve(params);
}

/**
 * Temporary method that blocks for a little while to simulate
 * waiting for canvas groups to be ready.
 *
 * TODO: replace this with a real request to lms/
 */
export async function groupsAsync() {
  return new Promise(resolve => {
    setTimeout(() => {
      resolve('groupsAsync resolved!');
    }, 500);
  });
}
