import Server from './server';
import { readyToReceive, requestConfig } from './methods';

let server = {}; // Singleton RPC server reference

/**
 * Create a new RPC server and pass in a the requestConfig object
 */
function startRpcServer() {
  server = new Server();
  server.register('requestConfig', requestConfig);
  server.register('readyToReceive', readyToReceive);
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

/**
 * Resolve the promise we created in the constructor with the saved
 * sidebar frame and origin.
 */
function setSidebarResolved() {
  server.resolveSidebarWindow({
    frame: server.currentFrameEvent.source,
    origin: server.currentFrameEvent.origin,
  });
}

export { startRpcServer, getSidebarWindow, setSidebarResolved };
