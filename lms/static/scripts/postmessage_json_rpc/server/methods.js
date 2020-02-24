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
