import classnames from 'classnames';
import { Route, Switch } from 'wouter-preact';

import CourseAssignmentsActivity from './CourseAssignmentsActivity';
import DashboardFooter from './DashboardFooter';
import StudentsActivity from './StudentsActivity';

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
            <Route path="/assignment/:assignmentId">
              <StudentsActivity />
            </Route>
            <Route path="/course/:courseId">
              <CourseAssignmentsActivity />
            </Route>
          </Switch>
        </div>
      </div>
      <DashboardFooter />
    </div>
  );
}
