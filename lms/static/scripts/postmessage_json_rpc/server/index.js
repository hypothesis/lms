import Server from './server';

let server = {}; // Singleton RPC server reference

/**
 * Create a new RPC server and register any methods it will support.
 *
 * @return {Server} - Instance of the server.
 */
function startRpcServer() {
  server = new Server();

  /**
   * Methods that are remotely callable by JSON-RPC over postMessage.
   *
   * Methods that can be remotely called by clients using our
   * JSON-RPC-over-postMessage server (postmessage_json_rpc/server/server.js) are
   * defined in one place in this module.
   */

  /**
   * Config request RPC handler.
   *
   * @returns {Object} - A Hypothesis client config object for the current LTI request.
   */
  server.register('requestConfig', () => {
    const configEl = document.querySelector('.js-config');
    const clientConfigObj = JSON.parse(configEl.textContent).hypothesisClient;
    return clientConfigObj;
  });

  /**
   * Section groups RPC handler.
   *
   * In the case where groups are not available at load time, the groups must
   * be fetched asynchronously using the api values found in the js-config
   * object. In order to speed this up even more, the groups are pre-loaded
   * before this RPC endpoint (`requestGroups`) is queried -- This method
   * simply returns an awaited promise to the client.
   *
   * @returns {Array} - List of groups
   */
  const groupsPromise = new Promise(resolve => {
    // This promise is resolved in BasicLtiLaunchApp after the
    // api request returns the groups.
    server.resolveGroupFetch = resolve;
  });
  server.register('requestGroups', async () => {
    return await groupsPromise;
  });

  return server;
}

/**
 * @typedef {Object} SidebarFrame
 * @prop {Window} frame - A reference to the window containing the sidebar application
 * @prop {string} origin - The sidebar window's origin
 */

/**
 * Gets the last used sidebar frame and origin.
 *
 * @returns {Promise<SidebarFrame>} - The `SidebarFrame`
 */
function getSidebarWindow() {
  return server.sidebarWindow;
}

export { startRpcServer, getSidebarWindow };
