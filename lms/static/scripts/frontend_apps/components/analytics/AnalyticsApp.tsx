import classnames from 'classnames';
import { useParams } from 'wouter-preact';

import { useFetch } from '../../utils/fetch';
import type { StudentsActivityTableProps } from './StudentsActivityTable';
import StudentsActivityTable from './StudentsActivityTable';

export default function AnalyticsApp() {
  const { assignmentId = 'unknown' } = useParams();
  const assignment = useFetch<StudentsActivityTableProps['assignment']>(
    `${assignmentId}_assignment`,
    () =>
      // Fake assignment ingo that loads after 300ms
      new Promise(resolve =>
        setTimeout(
          () =>
            resolve({
              name: 'Biology 101',
              id: assignmentId,
            }),
          300,
        ),
      ),
  );
  const users = useFetch<StudentsActivityTableProps['students']>(
    `${assignmentId}_students`,
    () =>
      // A fake list of users that loads after 600ms
      new Promise(resolve =>
        setTimeout(
          () =>
            resolve([
              {
                name: 'Jane Doe',
                annotations: 5,
                replies: 3,
                lastActivity: '2024-01-28',
              },
              {
                name: 'John Doe',
                annotations: 8,
                replies: 1,
                lastActivity: '2024-03-09',
              },
            ]),
          600,
        ),
      ),
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
          src="/static/images/email_header.png"
          className="h-10"
        />
      </div>
      <div className="mx-auto max-w-6xl">
        <StudentsActivityTable
          students={users.data ?? []}
          loading={users.isLoading}
          assignment={assignment.data}
        />
      </div>
    </div>
  );
}
