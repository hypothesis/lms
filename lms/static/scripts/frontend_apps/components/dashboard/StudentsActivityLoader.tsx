import { useCallback, useState } from 'preact/hooks';
import { useParams } from 'wouter-preact';

import type { Assignment, StudentStats } from '../../api-types';
import { useConfig } from '../../config';
import { apiCall } from '../../utils/api';
import { replaceURLParams } from '../../utils/url';
import DataLoader from '../DataLoader';
import type { StudentsActivityProps } from './StudentsActivity';
import StudentsActivity from './StudentsActivity';

export default function StudentsActivityLoader() {
  const { api, dashboard } = useConfig(['api', 'dashboard']);
  const { routes } = dashboard;
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const [responses, setResponses] = useState<StudentsActivityProps>();

  const load = useCallback(
    (signal: AbortSignal) =>
      Promise.all([
        apiCall<Assignment>({
          signal,
          authToken: api.authToken,
          path: replaceURLParams(routes.assignment, {
            assignment_id: assignmentId,
          }),
        }),
        apiCall<StudentStats[]>({
          signal,
          authToken: api.authToken,
          path: replaceURLParams(routes.assignment_stats, {
            assignment_id: assignmentId,
          }),
        }),
      ]).then(([assignment, students]) => ({ assignment, students })),
    [api.authToken, assignmentId, routes.assignment, routes.assignment_stats],
  );

  return (
    <DataLoader load={load} onLoad={setResponses} loaded={!!responses}>
      {responses && <StudentsActivity {...responses} />}
    </DataLoader>
  );
}
