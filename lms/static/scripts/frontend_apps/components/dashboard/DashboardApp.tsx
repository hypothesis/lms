import classnames from 'classnames';

import type { StudentStats, AssignmentStats } from '../../api-types';
import { useConfig } from '../../config';
import { useAPIFetch } from '../../utils/api';
import DashboardFooter from './DashboardFooter';
import {
  CourseAssignmentsTable,
  StudentsActivityTable,
} from './StudentsActivityTable';

export function DashboardAssignmentApp() {
  const { dashboard } = useConfig(['dashboard']);
  const { assignment, assignmentStatsApi } = dashboard;
  const students = useAPIFetch<StudentStats[]>(assignmentStatsApi.path);

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
          <StudentsActivityTable
            assignment={assignment}
            students={students.data ?? []}
            loading={students.isLoading}
          />
        </div>
      </div>
      <DashboardFooter />
    </div>
  );
}

export function DashboardCourseApp() {
  const { dashboard } = useConfig(['dashboard']);
  const { course, courseStatsApi } = dashboard;
  const assignments = useAPIFetch<AssignmentStats[]>(courseStatsApi.path);

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
          <CourseAssignmentsTable
            course={course}
            assignments={assignments.data ?? []}
            loading={assignments.isLoading}
          />
        </div>
      </div>
      <DashboardFooter />
    </div>
  );
}
