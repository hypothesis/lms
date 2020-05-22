// Polyfills.
import 'focus-visible';

// Setup app.
import { createElement, render } from 'preact';

import { Config } from './config';
import BasicLtiLaunchApp from './components/BasicLtiLaunchApp';
import FilePickerApp from './components/FilePickerApp';
import { startRpcServer } from '../postmessage_json_rpc/server';
import DialogTestsAndExamples from './components/DialogTestsAndExamples';

// Create an RPC Server and start listening to postMessage calls.
const rpcServer = startRpcServer();

const rootEl = document.querySelector('#app');
const config = JSON.parse(document.querySelector('.js-config').textContent);

config.mode = 'dialog-test';

render(
  <Config.Provider value={config}>
    {config.mode === 'dialog-test' && <DialogTestsAndExamples />}
    {config.mode === 'basic-lti-launch' && (
      <BasicLtiLaunchApp rpcServer={rpcServer} />
    )}
    {config.mode === 'content-item-selection' && <FilePickerApp />}
  </Config.Provider>,
  rootEl
);
