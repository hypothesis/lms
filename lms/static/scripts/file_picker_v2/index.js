import { createElement, render } from 'preact';

import { Config } from './config';
import FilePickerApp from './components/FilePickerApp';

const rootEl = document.querySelector('#app');
const config = JSON.parse(document.querySelector('.js-config').textContent);

render(
  <Config.Provider value={config}>
    <FilePickerApp />
  </Config.Provider>,
  rootEl
);
