// Entry point for local webserver pattern-library bundle
import { startApp } from '@hypothesis/frontend-shared/lib/pattern-library';
import type { CustomPlaygroundRoute } from '@hypothesis/frontend-shared/lib/pattern-library/routes';

// LMS prototype pages should be defined here
const extraRoutes: CustomPlaygroundRoute[] = [];

startApp({
  baseURL: '/ui-playground',
  extraRoutes,
  extraRoutesTitle: 'LMS UI',
});
