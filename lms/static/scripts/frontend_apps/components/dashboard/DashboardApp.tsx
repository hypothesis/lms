import classnames from 'classnames';
import { Route, Switch } from 'wouter-preact';

import AssignmentActivity from './AssignmentActivity';
import CourseActivity from './CourseActivity';
import DashboardFooter from './DashboardFooter';

export default function DashboardApp() {
  return (
    <div className="flex flex-col min-h-screen gap-5 bg-grey-2">
      <div
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
          </Switch>
        </div>
      </div>
      <DashboardFooter />
    </div>
  );
}
