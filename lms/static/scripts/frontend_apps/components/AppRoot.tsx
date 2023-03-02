import { useState } from 'preact/hooks';
import { Route, Switch } from 'wouter-preact';

import type { ConfigObject } from '../config';
import { Config } from '../config';
import type { ServiceMap } from '../services';
import { Services } from '../services';
import BasicLTILaunchApp from './BasicLTILaunchApp';
import DataLoader from './DataLoader';
import ErrorDialogApp from './ErrorDialogApp';
import FilePickerApp from './FilePickerApp';
import OAuth2RedirectErrorApp from './OAuth2RedirectErrorApp';

export type AppRootProps = {
  /** Initial route and configuration for the frontend, read from the HTML page. */
  initialConfig: ConfigObject;
  services: ServiceMap;
};

/**
 * Return dummy configuration for the file picker app. This will be replaced
 * with a call to the endpoint created in https://github.com/hypothesis/lms/pull/5120.
 */
/* istanbul ignore next */
async function loadDummyFilePickerConfig(
  config: ConfigObject
): Promise<ConfigObject> {
  // Add a fake delay so we can see the loading state initially.
  await new Promise(resolve => setTimeout(resolve, 1000));

  // Allow `simulateError` global to be set to trigger an error here.
  if ((window as any).simulateError) {
    throw new Error('Failed to load file picker config');
  }

  const apiCallInfo = { path: '/api/dummy' };

  return {
    ...config,
    product: {
      family: 'dummy',
      api: {
        listGroupSets: apiCallInfo,
      },
      settings: { groupsEnabled: false },
    },
    filePicker: {
      formAction: 'dummy',
      formFields: {},
      ltiLaunchUrl: 'dummy',
      blackboard: {
        enabled: false,
        listFiles: apiCallInfo,
      },
      d2l: {
        enabled: false,
        listFiles: apiCallInfo,
      },
      canvas: {
        enabled: false,
        listFiles: apiCallInfo,
      },
      google: {
        clientId: 'dummy',
        developerKey: 'dummy',
        origin: 'dummy',
      },
      jstor: {
        enabled: false,
      },
      microsoftOneDrive: {
        enabled: false,
        clientId: 'dummy',
        redirectURI: 'dummy',
      },
      vitalSource: {
        enabled: false,
      },
    },
  };
}

/**
 * The root component for the LMS frontend.
 */
export default function AppRoot({ initialConfig, services }: AppRootProps) {
  const [config, setConfig] = useState(initialConfig);

  return (
    <Config.Provider value={config}>
      <Services.Provider value={services}>
        <Switch>
          <Route path="/app/basic-lti-launch">
            <BasicLTILaunchApp />
          </Route>
          <Route path="/app/content-item-selection">
            <DataLoader
              load={
                /* istanbul ignore next */
                () => loadDummyFilePickerConfig(config)
              }
              onLoad={setConfig}
              isLoaded={'filePicker' in config}
            >
              <FilePickerApp />
            </DataLoader>
          </Route>
          <Route path="/app/error-dialog">
            <ErrorDialogApp />
          </Route>
          <Route path="/app/oauth2-redirect-error">
            <OAuth2RedirectErrorApp />
          </Route>
          <Route>
            <div data-testid="notfound-message">Page not found</div>
          </Route>
        </Switch>
      </Services.Provider>
    </Config.Provider>
  );
}
