import 'focus-visible';
import { createElement, render } from 'preact';

import { readConfig, Config } from './config';
import BasicLtiLaunchApp from './components/BasicLtiLaunchApp';
import CanvasOAuth2RedirectErrorApp from './components/CanvasOAuth2RedirectErrorApp';
import FilePickerApp from './components/FilePickerApp';
import { ClientRpc } from './services/client-rpc';
import { GradingService, Services } from './services';

/** @typedef {import('./services/client-rpc').ClientConfig} ClientConfig */

import { registerIcons } from '@hypothesis/frontend-shared';
import iconSet from './icons';
registerIcons(iconSet);

// Read configuration embedded into page by backend.
const config = readConfig();

// Create services.
const services = new Map(
  /** @type {[Function, any][]} */ ([
    [GradingService, new GradingService({ authToken: config.api.authToken })],
  ])
);

// Render main component for current route.
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

// Render frontend application.
const rootEl = document.querySelector('#app');
if (!rootEl) {
  throw new Error('#app container for LMS frontend is missing');
}
render(
  <Config.Provider value={config}>
    <Services.Provider value={services}>{app}</Services.Provider>
  </Config.Provider>,
  rootEl
);
