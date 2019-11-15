import Server from './server';
import { requestConfig } from './methods';

let server = {}; // Singleton RPC server reference

/**
 * Create a new RPC server and pass in a the requestConfig object
 */
function startRpcServer() {
  server = new Server();
  server.register('requestConfig', requestConfig);
}

/**
 * @typedef {Object} SidebarFrame
 * @prop {Window} frame - A reference to the window containing the sidebar application
 * @prop {string} origin - The sidebar window's origin
 */

/**
 * Gets the last used sidebar frame and origin.
 *
 * @returns {SidebarFrame}
 */
function getSidebarWindow() {
  if(server._sidebarWindow) {
    return Promise.resolve(server._sidebarWindow);
  }
  else {
    return new Promise((resolve, reject) => {
      _sidebarWindowLoaded
    })
  }
  //return server._sidebarWindow;
}

export { startRpcServer, getSidebarWindow };
