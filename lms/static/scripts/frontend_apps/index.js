import 'focus-visible';
import { createElement, render } from 'preact';

import { readConfig, Config } from './config';
import BasicLtiLaunchApp from './components/BasicLtiLaunchApp';
import CanvasOAuth2RedirectErrorApp from './components/CanvasOAuth2RedirectErrorApp';
import FilePickerApp from './components/FilePickerApp';
import { ClientRpc, GradingService, Services } from './services';

/** @typedef {import('./services/client-rpc').ClientConfig} ClientConfig */

import { registerIcons } from '@hypothesis/frontend-shared';
import iconSet from './icons';
registerIcons(iconSet);

// Read configuration embedded into page by backend.
const config = readConfig();

/**
 * Directory of services used by the current application.
 *
 * The necessary services for the different app types are currently initialized
 * manually before rendering. If we end up with many services in future we may
 * want to move to initializing them on-demand instead.
 *
 * @type {import('./services').ServiceMap}
 */
const services = new Map();

// Render main component for current route.
let app;
switch (config.mode) {
  case 'basic-lti-launch':
    services.set(
      ClientRpc,
      new ClientRpc({
        authToken: config.api.authToken,
        allowedOrigins: config.rpcServer.allowedOrigins,
        clientConfig: /** @type {ClientConfig} */ (config.hypothesisClient),
      })
    );
    services.set(
      GradingService,
      new GradingService({ authToken: config.api.authToken })
    );
    app = <BasicLtiLaunchApp />;
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
