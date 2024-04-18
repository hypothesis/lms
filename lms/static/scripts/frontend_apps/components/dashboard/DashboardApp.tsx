import classnames from 'classnames';
import { useParams } from 'wouter-preact';

import type { StudentStats } from '../../api-types';
import { useConfig } from '../../config';
import { apiCall } from '../../utils/api';
import { useFetch } from '../../utils/fetch';
import StudentsActivityTable from './StudentsActivityTable';

export default function DashboardApp() {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const { dashboard, api } = useConfig(['dashboard', 'api']);
  const assignment = {
    title: dashboard.assignment.title,
    id: assignmentId,
  };
  const students = useFetch<StudentStats[]>(`${assignmentId}_students`, () =>
    apiCall({
      authToken: api.authToken,
      method: 'GET',
      path: dashboard.assignmentStatsApi.path,
    }),
  );

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
          src="/static/images/hypothesis_logo.png"
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
