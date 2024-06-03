import { useState } from 'preact/hooks';
import { Route, Switch } from 'wouter-preact';

import type { ConfigObject } from '../config';
import { Config } from '../config';
import type { ServiceMap } from '../services';
import { Services } from '../services';
import BasicLTILaunchApp from './BasicLTILaunchApp';
import DataLoader from './DataLoader';
import EmailPreferencesApp from './EmailPreferencesApp';
import ErrorDialogApp from './ErrorDialogApp';
import FilePickerApp, { loadFilePickerConfig } from './FilePickerApp';
import OAuth2RedirectErrorApp from './OAuth2RedirectErrorApp';
import DashboardApp from './dashboard/DashboardApp';

export type AppRootProps = {
  /** Initial route and configuration for the frontend, read from the HTML page. */
  initialConfig: ConfigObject;
  services: ServiceMap;
};

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
              load={() => loadFilePickerConfig(config)}
              onLoad={setConfig}
              loaded={'filePicker' in config}
            >
              <FilePickerApp />
            </DataLoader>
          </Route>
          <Route path="/dashboard/organizations/:organizationPublicId" nest>
            <DashboardApp />
          </Route>
          <Route path="/email/preferences">
            <EmailPreferencesApp />
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
