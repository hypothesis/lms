import { useEffect, useState } from 'preact/hooks';

import type { AppMode, ConfigObject } from '../config';
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

const APP_MODES: readonly AppMode[] = [
  'basic-lti-launch',
  'content-item-selection',
  'error-dialog',
  'oauth2-redirect-error',
] as const;

export default function AppRoot({ initialConfig, services }: AppRootProps) {
  const [config, setConfig] = useState(initialConfig);
  config.update = (newConfig: Partial<ConfigObject>) => {
    setConfig({ ...config, ...newConfig });
  };

  // Preserve the current frontend app mode in the window hash. This allows
  // the browser's back button to work for eg. transitioning from editing an
  // assignment back to viewing it.
  //
  // It would nice nicer to use proper URLs.
  useEffect(() => {
    const onHashChange = (event: HashChangeEvent) => {
      const mode = new URL(event.newURL).hash.slice(1) as AppMode;
      if (!APP_MODES.includes(mode)) {
        return;
      }

      setConfig(config => {
        if (config.mode === mode) {
          return config;
        }
        return { ...config, mode };
      });
    };
    window.addEventListener('hashchange', onHashChange);
    return () => {
      window.removeEventListener('hashchange', onHashChange);
    };
  }, []);

  useEffect(() => {
    window.location.hash = config.mode;
  }, [config.mode]);

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
