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
