import { apiCall } from '../../frontend_apps/utils/api';

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
 * In the case where groups are not available at load time, the groups must
 * be fetched asynchronously using the api values found in the js-config
 * object. In this case, call the remote endpoint and return the groups for
 * the Hypothesis client.
 */
export async function requestGroups() {
  const configObj = JSON.parse(
    document.querySelector('.js-config').textContent
  );
  return apiCall({
    authToken: configObj.api.authToken,
    path: configObj.api.sync.path,
    data: configObj.api.sync.data,
  });
}
