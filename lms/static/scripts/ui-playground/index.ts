// Entry point for local webserver pattern-library bundle
import { startApp } from '@hypothesis/frontend-shared/lib/pattern-library';
import type { CustomPlaygroundRoute } from '@hypothesis/frontend-shared/lib/pattern-library/routes';

import GradeStatusChipPage from './components/GradeStatusChipPage';

// LMS prototype pages should be defined here
const extraRoutes: CustomPlaygroundRoute[] = [
  {
    component: GradeStatusChipPage,
    route: '/grade-status-chip',
    title: 'Grade status chip',
  },
];

startApp({
  baseURL: '/ui-playground',
  extraRoutes,
  extraRoutesTitle: 'LMS UI',
});
