// Entry point for local webserver pattern-library bundle
import { startApp } from '@hypothesis/frontend-shared/lib/pattern-library';

import lmsIcons from '../frontend_apps/icons.js';

startApp({
  baseURL: '/ui-playground',
  icons: lmsIcons,
});
