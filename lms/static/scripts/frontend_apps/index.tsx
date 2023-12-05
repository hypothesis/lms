import 'focus-visible';
import { render } from 'preact';
// Enable debugging checks and devtools. Removed in prod builds by Rollup config.
import 'preact/debug';

import AppRoot from './components/AppRoot';
import type { AppMode } from './config';
import { readConfig } from './config';
import {
  ClientRPC,
  ContentInfoFetcher,
  GradingService,
  VitalSourceService,
} from './services';
import type { ServiceMap } from './services';

function routeForAppMode(mode: AppMode): string {
  if (mode === 'email-notifications') {
    // For the email-notifications mode, since this app is not designed to be
    // opened in an iframe, but as the main window frame, we want to use a route
    // that matches the server-side one.
    return '/email/preferences';
  }

  return `/app/${mode}`;
}

export function init() {
  // Read configuration embedded into page by backend.
  const config = readConfig();

  /**
   * Directory of services used by the current application.
   *
   * The necessary services for the different app types are currently initialized
   * manually before rendering. If we end up with many services in future we may
   * want to move to initializing them on-demand instead.
   */
  const services: ServiceMap = new Map();

  if (config.debug?.values && Object.keys(config.debug.values).length) {
    /* eslint-disable no-console */
    console.groupCollapsed('Hypothesis debug info');
    Object.entries(config.debug.values).forEach(([key, value]) =>
      console.log(key + ': ' + value)
    );
    console.groupEnd();
    /* eslint-enable no-console */
  }

  // Construct services used by the file picker app. We need this both for
  // direct launches into this app, and for transitions from viewing to
  // editing assignments.
  if (config.api?.authToken) {
    services.set(
      VitalSourceService,
      new VitalSourceService({ authToken: config.api.authToken })
    );
  }

  if (config.api && config.rpcServer && config.hypothesisClient) {
    const { authToken } = config.api;
    const clientRPC = new ClientRPC({
      authToken,
      allowedOrigins: config.rpcServer.allowedOrigins,
      clientConfig: /** @type {ClientConfig} */ config.hypothesisClient,
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
  }

  // Set route based on app mode.
  const routePath = routeForAppMode(config.mode);
  if (location.pathname !== routePath) {
    history.replaceState({}, 'unused', routePath);
  }

  // Render frontend application.
  const rootEl = document.querySelector('#app');
  /* istanbul ignore next */
  if (!rootEl) {
    throw new Error('#app container for LMS frontend is missing');
  }

  render(<AppRoot initialConfig={config} services={services} />, rootEl);
}

/* istanbul ignore next */
// @ts-expect-error - Ignore LMS_FRONTEND_TESTS global set by Rollup
if (typeof LMS_FRONTEND_TESTS === 'undefined') {
  init();
}
