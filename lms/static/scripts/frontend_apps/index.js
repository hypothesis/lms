// Polyfills.
import 'focus-visible';

// Setup app.
import { createElement, render } from 'preact';

import { readConfig, Config } from './config';
import BasicLtiLaunchApp from './components/BasicLtiLaunchApp';
import CanvasOAuth2RedirectErrorApp from './components/CanvasOAuth2RedirectErrorApp';
import FilePickerApp from './components/FilePickerApp';
import { ClientRpc } from './services/client-rpc';

/** @typedef {import('./services/client-rpc').ClientConfig} ClientConfig */

const rootEl = document.querySelector('#app');
if (!rootEl) {
  throw new Error('#app container for LMS frontend is missing');
}

const config = readConfig();

import { registerIcons } from './components/SvgIcon';
import iconSet from './icons';
registerIcons(iconSet);

let app;
switch (config.mode) {
  case 'basic-lti-launch':
    app = (
      <BasicLtiLaunchApp
        clientRpc={
          new ClientRpc({
            authToken: config.api.authToken,
            allowedOrigins: config.rpcServer.allowedOrigins,
            clientConfig: /** @type {ClientConfig} */ (config.hypothesisClient),
          })
        }
      />
    );
    break;
  case 'content-item-selection':
    app = <FilePickerApp />;
    break;
  case 'canvas-oauth2-redirect-error':
    app = <CanvasOAuth2RedirectErrorApp />;
    break;
}

render(<Config.Provider value={config}>{app}</Config.Provider>, rootEl);
