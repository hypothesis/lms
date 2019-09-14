// Polyfills.
import 'focus-visible';

// Setup app.
import { createElement, render } from 'preact';

import { Config } from './config';
import BasicLtiLaunchApp from './components/BasicLtiLaunchApp';
import FilePickerApp from './components/FilePickerApp';

const rootEl = document.querySelector('#app');
const config = JSON.parse(document.querySelector('.js-lms-config').textContent);

const mode = config.mode || 'content-item-selection';

config.students = [
  {
    name: 'Student 1',
  },
  {
    name: 'Student 2',
  },
]; // Temporary fix until we add this in python

render(
  <Config.Provider value={config}>
    {mode === 'basic-lti-launch' && <BasicLtiLaunchApp />}
    {mode === 'content-item-selection' && <FilePickerApp />}
  </Config.Provider>,
  rootEl
);
