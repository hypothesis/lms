import classnames from 'classnames';

import type { StudentStats } from '../../api-types';
import { useConfig } from '../../config';
import { useAPIFetch } from '../../utils/api';
import DashboardFooter from './DashboardFooter';
import StudentsActivityTable from './StudentsActivityTable';

export default function DashboardApp() {
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
          src="/static/images/hypothesis_wordmark_logo.png"
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
