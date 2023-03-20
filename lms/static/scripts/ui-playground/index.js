// Entry point for local webserver pattern-library bundle
import { startApp } from '@hypothesis/frontend-shared/lib/pattern-library';

import EditAssignmentPage from './components/EditAssignment';
import ErrorComponents from './components/ErrorComponents';
import ToolbarPage from './components/ToolbarPage';

/** @type {import('@hypothesis/frontend-shared/lib/pattern-library').PlaygroundRoute[]} */
const extraRoutes = [
  {
    route: '/edit-assignment',
    title: 'Edit Assignment',
    component: EditAssignmentPage,
  },
  {
    route: '/errors',
    title: 'Errors',
    component: ErrorComponents,
  },
  {
    route: '/toolbar',
    title: 'Toolbar',
    component: ToolbarPage,
  },
];

startApp({
  baseURL: '/ui-playground',
  extraRoutes,
  extraRoutesTitle: 'LMS UI',
});
