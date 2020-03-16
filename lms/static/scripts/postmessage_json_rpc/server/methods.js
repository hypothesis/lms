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
 * Return the groups for the Hypothesis client to show.
 */
export async function requestGroups() {
  const configObj = JSON.parse(
    document.querySelector('.js-config').textContent
  );

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  if (configObj.dev === true) {
    // Artifically sleep to simulate how long this will take when it needs to
    // send real API requests to get the groups.
    // The artificial delay is only inserted 50% of the time (at random) so we
    // don't somehow accidentally end up relying on the slowness.
    if (Math.random() < 0.5) {
      await sleep(1900);
    }
  }

  return configObj.hypothesisClient.services[0].groups;
}
