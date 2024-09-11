import {
  Button,
  LeaveIcon,
  SpinnerCircleIcon,
} from '@hypothesis/frontend-shared';
import { useCallback, useMemo, useState } from 'preact/hooks';
import { useParams } from 'wouter-preact';

import type { GradingSync } from '../../api-types';
import { useConfig } from '../../config';
import { apiCall, usePolledAPIFetch } from '../../utils/api';
import type { QueryParams } from '../../utils/url';
import { replaceURLParams } from '../../utils/url';

export type SyncGradesButtonProps = {
  /**
   * List of students and their grades, which should be synced when the button
   * is clicked.
   */
  studentsToSync: Array<{ h_userid: string; grade: number }>;
};

export default function SyncGradesButton({
  studentsToSync,
}: SyncGradesButtonProps) {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const { dashboard, api } = useConfig(['dashboard', 'api']);
  const { routes } = dashboard;
  const [syncing, setSyncing] = useState(false);

  const syncUrl = useMemo(
    () =>
      replaceURLParams(routes.assignment_grades_sync ?? ':assignment_id', {
        assignment_id: assignmentId,
      }),
    [assignmentId, routes.assignment_grades_sync],
  );
  const [lastSyncParams, setLastSyncParams] = useState<QueryParams>({});
  const lastSync = usePolledAPIFetch<GradingSync>({
    path: syncUrl,
    params: lastSyncParams,
    // Keep polling as long as sync is in progress
    shouldRefresh: result =>
      !!result.data &&
      ['scheduled', 'in_progress'].includes(result.data.status),
  });

  const buttonContent = useMemo(() => {
    if (lastSync.isLoading) {
      return 'Loading...';
    }

    if (
      syncing ||
      (lastSync.data &&
        ['scheduled', 'in_progress'].includes(lastSync.data.status))
    ) {
      return (
        <>
          Syncing grades
          <SpinnerCircleIcon className="ml-1.5" />
        </>
      );
    }

    // TODO Maybe these two should be represented differently
    if (lastSync.error || lastSync.data?.status === 'failed') {
      return (
        <>
          Error syncing. Click to retry
          <LeaveIcon />
        </>
      );
    }

    if (studentsToSync.length > 0) {
      return `Sync ${studentsToSync.length} students`;
    }

    return 'Grades synced';
  }, [
    lastSync.isLoading,
    lastSync.data,
    lastSync.error,
    syncing,
    studentsToSync.length,
  ]);

  const buttonDisabled = useMemo(
    () => syncing || lastSync.isLoading || studentsToSync.length === 0,
    [syncing, lastSync.isLoading, studentsToSync.length],
  );

  const syncGrades = useCallback(async () => {
    setSyncing(true);

    await apiCall({
      authToken: api.authToken,
      path: syncUrl,
      method: 'POST',
      data: { grades: studentsToSync },
    }).finally(() => setSyncing(false));

    // Once the request succeeds, we update the params so that polling the
    // status is triggered again
    setLastSyncParams({ t: `${Date.now()}` });
  }, [api.authToken, studentsToSync, syncUrl]);

  return (
    <Button variant="primary" onClick={syncGrades} disabled={buttonDisabled}>
      {buttonContent}
    </Button>
  );
}
