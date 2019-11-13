import Server from './server';
import { requestConfig } from './methods';

let server = {}; // Singleton rpc server reference

/**
 * Create a new RPC server and pass in a the requestConfig object
 */
function startRpcServer() {
  server = new Server();
  server.register('requestConfig', requestConfig);
}

/**
 * @typedef {Object} SidebarFrame
 * @prop {Object} frame - The reference to the sidebar window
 * @prop {string} origin - The sidebar window's origin uri
 */

/**
 * Gets the last used sidebar frame and origin.
 *
 * @returns {SidebarFrame}
 */
function getSidebarWindow() {
  return server._sidebarWindow;
}

export { startRpcServer, getSidebarWindow };
