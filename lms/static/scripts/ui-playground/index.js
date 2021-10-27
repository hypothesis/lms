// Entry point for local webserver pattern-library bundle
import { startApp } from '@hypothesis/frontend-shared/lib/pattern-library';

import ErrorComponents from './components/ErrorComponents';

import lmsIcons from '../frontend_apps/icons.js';

/** @type {import('@hypothesis/frontend-shared/lib/pattern-library').PlaygroundRoute[]} */
const extraRoutes = [
  {
    route: '/errors',
    title: 'Errors',
    component: ErrorComponents,
    group: 'components',
  },
];

startApp({
  baseURL: '/ui-playground',
  extraRoutes,
  icons: lmsIcons,
});
