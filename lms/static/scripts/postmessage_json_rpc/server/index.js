import Server from './server';
import { requestConfig } from './methods';

let server = {}; // Singleton RPC server reference

/**
 * Create a new RPC server and register any methods it will support.
 *
 * @return {Server} - Instance of the server.
 */
function startRpcServer() {
  server = new Server();
  server.register('requestConfig', requestConfig);

  /**
   * In the case where groups are not available at load time, the groups must
   * be fetched asynchronously using the api values found in the js-config
   * object. In order to speed this up even more, the groups are pre-loaded
   * before this RPC endpoint (`requestGroups`) is queried -- This method
   * simply returns an awaited promise to the client.
   */
  const groupsPromise = new Promise(resolve => {
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
