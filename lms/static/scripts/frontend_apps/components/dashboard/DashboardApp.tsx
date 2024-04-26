import classnames from 'classnames';

import type { StudentStats } from '../../api-types';
import { useConfig } from '../../config';
import { useAPIFetch } from '../../utils/api';
import StudentsActivityTable from './StudentsActivityTable';

export default function DashboardApp() {
  const { dashboard } = useConfig(['dashboard']);
  const { assignment, assignmentStatsApi } = dashboard;
  const students = useAPIFetch<StudentStats[]>(assignmentStatsApi.path);

  return (
    <div className="min-h-full bg-grey-2">
      <div
        className={classnames(
          'flex justify-center p-3 mb-5 w-full',
          'bg-white border-b shadow',
        )}
      >
        <img
          alt="Hypothesis logo"
          src="/static/images/hypothesis-wordmark-logo.png"
          className="h-10"
        />
      </div>
      <div className="mx-auto max-w-6xl">
        <StudentsActivityTable
          assignment={assignment}
          students={students.data ?? []}
          loading={students.isLoading}
        />
      </div>
    </div>
  );
}
