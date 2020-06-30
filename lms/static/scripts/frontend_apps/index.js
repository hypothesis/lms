// Polyfills.
import 'focus-visible';

// Setup app.
import { createElement, render } from 'preact';

import { Config } from './config';
import BasicLtiLaunchApp from './components/BasicLtiLaunchApp';
import CanvasOAuth2RedirectErrorApp from './components/CanvasOAuth2RedirectErrorApp';
import FilePickerApp from './components/FilePickerApp';
import { startRpcServer } from '../postmessage_json_rpc/server';

const rootEl = document.querySelector('#app');
const config = JSON.parse(document.querySelector('.js-config').textContent);

let rpcServer;
if (config.mode === 'basic-lti-launch') {
  // Create an RPC Server and start listening to postMessage calls.
  rpcServer = startRpcServer();
}

render(
  <Config.Provider value={config}>
    {config.mode === 'basic-lti-launch' && (
      <BasicLtiLaunchApp rpcServer={rpcServer} />
    )}
    {config.mode === 'content-item-selection' && <FilePickerApp />}
    {config.mode === 'canvas-oauth2-redirect-error' && (
      <CanvasOAuth2RedirectErrorApp />
    )}
  </Config.Provider>,
  rootEl
);
