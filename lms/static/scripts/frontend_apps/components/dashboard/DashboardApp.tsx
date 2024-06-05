import classnames from 'classnames';
import { Route, Switch, useParams } from 'wouter-preact';

import HideUntilLoad from '../HideUntilLoad';
import AssignmentActivity from './AssignmentActivity';
import CourseActivity from './CourseActivity';
import DashboardFooter from './DashboardFooter';
import OrganizationActivity from './OrganizationActivity';

export default function DashboardApp() {
  const { organizationPublicId } = useParams<{
    organizationPublicId: string;
  }>();

  return (
    <div className="flex flex-col min-h-screen bg-grey-2">
      <header
        className={classnames(
          'flex justify-center p-3 w-full',
          'bg-white border-b shadow',
        )}
      >
        <img
          alt="Hypothesis logo"
          src="/static/images/hypothesis-wordmark-logo.png"
          className="h-10"
        />
      </header>
      <HideUntilLoad classes="flex-grow" footer={<DashboardFooter />}>
        <Switch>
          <Route path="/assignments/:assignmentId">
            <AssignmentActivity />
          </Route>
          <Route path="/courses/:courseId">
            <CourseActivity />
          </Route>
          <Route path="">
            <OrganizationActivity organizationPublicId={organizationPublicId} />
          </Route>
        </Switch>
      </HideUntilLoad>
    </div>
  );
}
