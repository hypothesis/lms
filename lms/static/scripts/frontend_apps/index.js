// Polyfills.
import 'focus-visible';

// Setup app.
import { createElement, render } from 'preact';

import { readConfig, Config } from './config';
import BasicLtiLaunchApp from './components/BasicLtiLaunchApp';
import CanvasOAuth2RedirectErrorApp from './components/CanvasOAuth2RedirectErrorApp';
import FilePickerApp from './components/FilePickerApp';
import { ClientRpc } from './services/client-rpc';

const rootEl = document.querySelector('#app');
if (!rootEl) {
  throw new Error('#app container for LMS frontend is missing');
}

const config = readConfig();

import { registerIcons } from './components/SvgIcon';
import iconSet from './icons';
registerIcons(iconSet);

render(
  <Config.Provider value={config}>
    {config.mode === 'basic-lti-launch' && (
      <BasicLtiLaunchApp
        clientRpc={
          new ClientRpc({
            allowedOrigins: config.rpcServer.allowedOrigins,
            clientConfig: config.hypothesisClient,
          })
        }
      />
    )}
    {config.mode === 'content-item-selection' && <FilePickerApp />}
    {config.mode === 'canvas-oauth2-redirect-error' && (
      <CanvasOAuth2RedirectErrorApp />
    )}
  </Config.Provider>,
  rootEl
);
