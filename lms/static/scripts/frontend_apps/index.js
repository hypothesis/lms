// Polyfills.
import 'focus-visible';

// Setup app.
import { createElement, render } from 'preact';

import { Config } from './config';
import BasicLtiLaunchApp from './components/BasicLtiLaunchApp';
import FilePickerApp from './components/FilePickerApp';
import { startRpcServer } from '../postmessage_json_rpc/server';

// Create an RPC Server and start listening to postMessage calls.
startRpcServer();

const rootEl = document.querySelector('#app');
const config = JSON.parse(document.querySelector('.js-lms-config').textContent);

const mode = config.mode || 'content-item-selection';

render(
  <Config.Provider value={config}>
    {mode === 'basic-lti-launch' && <BasicLtiLaunchApp />}
    {mode === 'content-item-selection' && <FilePickerApp />}
  </Config.Provider>,
  rootEl
);
