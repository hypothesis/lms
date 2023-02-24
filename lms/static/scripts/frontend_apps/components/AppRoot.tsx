import { useState } from 'preact/hooks';

import type { ConfigObject } from '../config';
import { Config } from '../config';
import type { ServiceMap } from '../services';
import { Services } from '../services';

import BasicLTILaunchApp from './BasicLTILaunchApp';
import OAuth2RedirectErrorApp from './OAuth2RedirectErrorApp';
import ErrorDialogApp from './ErrorDialogApp';
import FilePickerApp from './FilePickerApp';

export type AppRootProps = {
  initialConfig: ConfigObject;
  services: ServiceMap;
};

export default function AppRoot({ initialConfig, services }: AppRootProps) {
  const [config, setConfig] = useState(initialConfig);
  config.update = (newConfig: Partial<ConfigObject>) => {
    setConfig({ ...config, ...newConfig });
  };

  let root;
  switch (config.mode) {
    case 'basic-lti-launch':
      root = <BasicLTILaunchApp />;
      break;
    case 'content-item-selection':
      root = <FilePickerApp />;
      break;
    case 'error-dialog':
      root = <ErrorDialogApp />;
      break;
    case 'oauth2-redirect-error':
      root = <OAuth2RedirectErrorApp />;
      break;
    default:
      throw new Error(`Unknown frontend app ${config.mode}`);
  }

  return (
    <Config.Provider value={config}>
      <Services.Provider value={services}>{root}</Services.Provider>
    </Config.Provider>
  );
}
