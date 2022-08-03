import 'focus-visible';
import { render } from 'preact';

import { readConfig, Config } from './config';
import BasicLTILaunchApp from './components/BasicLTILaunchApp';
import OAuth2RedirectErrorApp from './components/OAuth2RedirectErrorApp';
import ErrorDialogApp from './components/ErrorDialogApp';
import FilePickerApp from './components/FilePickerApp';
import {
  ClientRPC,
  ContentInfoFetcher,
  GradingService,
  Services,
  VitalSourceService,
} from './services';

/** @typedef {import('./services/client-rpc').ClientConfig} ClientConfig */

import { registerIcons } from '@hypothesis/frontend-shared';
import iconSet from './icons';
registerIcons(iconSet);

export function init() {
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
      {
        const { authToken } = config.api;
        const clientRPC = new ClientRPC({
          authToken,
          allowedOrigins: config.rpcServer.allowedOrigins,
          clientConfig: /** @type {ClientConfig} */ (config.hypothesisClient),
        });
        const contentInfoFetcher = new ContentInfoFetcher(authToken, clientRPC);
        const gradingService = new GradingService({
          authToken: config.api.authToken,
        });
        services.set(ClientRPC, clientRPC);
        services.set(ContentInfoFetcher, contentInfoFetcher);
        services.set(GradingService, gradingService);

        if (config.contentBanner) {
          // Fetch data for content info banner displayed by the client. If this
          // fails, the banner won't be shown but everything else should
          // continue to work.
          contentInfoFetcher.fetch(config.contentBanner);
        }

        app = <BasicLTILaunchApp />;
      }
      break;
    case 'content-item-selection':
      services.set(
        VitalSourceService,
        new VitalSourceService({ authToken: config.api.authToken })
      );
      app = <FilePickerApp />;
      break;
    case 'error-dialog':
      app = <ErrorDialogApp />;
      break;
    case 'oauth2-redirect-error':
      app = <OAuth2RedirectErrorApp />;
      break;
  }

  // Render frontend application.
  const rootEl = document.querySelector('#app');
  /* istanbul ignore next */
  if (!rootEl) {
    throw new Error('#app container for LMS frontend is missing');
  }

  render(
    <Config.Provider value={config}>
      <Services.Provider value={services}>{app}</Services.Provider>
    </Config.Provider>,
    rootEl
  );
}

/* istanbul ignore next */
// @ts-expect-error - Ignore LMS_FRONTEND_TESTS global set by Rollup
if (typeof LMS_FRONTEND_TESTS === 'undefined') {
  init();
}
