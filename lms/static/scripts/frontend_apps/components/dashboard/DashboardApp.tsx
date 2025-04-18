import { LogoIcon, ProfileIcon } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { Link as RouterLink, Route, Switch } from 'wouter-preact';

import { useConfig } from '../../config';
import { usePlaceholderDocumentTitleInDev } from '../../utils/hooks';
import AllCoursesActivity from './AllCoursesActivity';
import AssignmentActivity from './AssignmentActivity';
import CourseActivity from './CourseActivity';
import DashboardFooter from './DashboardFooter';

export default function DashboardApp() {
  const { dashboard } = useConfig(['dashboard']);

  usePlaceholderDocumentTitleInDev();

  return (
    <div className="flex flex-col min-h-screen gap-5">
      <div className="px-3 py-4 bg-white border-b shadow">
        <div className="flex justify-between items-center mx-auto max-w-6xl">
          <RouterLink href="" aria-label="All courses">
            <LogoIcon className="w-6 h-6" />
          </RouterLink>

          <div className="flex gap-6">
            <span
              className={classnames(
                'flex gap-2 items-center',
                'font-semibold text-color-text-light',
              )}
              data-testid="display-name"
            >
              <ProfileIcon />
              {dashboard.user.display_name}
            </span>
          </div>
        </div>
      </div>
      <div className="flex-grow px-3">
        <div className="mx-auto max-w-6xl">
          <Switch>
            <Route path="/assignments/:assignmentId">
              <AssignmentActivity />
            </Route>
            <Route path="/courses/:courseId">
              <CourseActivity />
            </Route>
            <Route path="">
              <AllCoursesActivity />
            </Route>
          </Switch>
        </div>
      </div>
      <DashboardFooter />
    </div>
  );
}
