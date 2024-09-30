import {
  Button,
  LeaveIcon,
  SpinnerCircleIcon,
} from '@hypothesis/frontend-shared';
import { useCallback, useMemo } from 'preact/hooks';
import { useParams } from 'wouter-preact';

import type { GradingSync, GradingSyncStatus } from '../../api-types';
import { useConfig } from '../../config';
import { APIError } from '../../errors';
import { apiCall } from '../../utils/api';
import type { FetchResult } from '../../utils/fetch';
import { replaceURLParams } from '../../utils/url';

export type SyncGradesButtonProps = {
  /**
   * List of students and their grades, which should be synced when the button
   * is clicked.
   * Passing `undefined` means students are not yet known and/or being loaded.
   */
  studentsToSync?: Array<{ h_userid: string; grade: number }>;

  /**
   * Invoked after a sync was scheduled successfully.
   * This being invoked doesn't ensure syncs will succeed, only that they were
   * properly scheduled.
   */
  onSyncScheduled: () => void;

  /** Result of fetching the status of last sync */
  lastSync: FetchResult<GradingSync>;
};

export default function SyncGradesButton({
  studentsToSync,
  onSyncScheduled,
  lastSync,
}: SyncGradesButtonProps) {
  const { assignmentId } = useParams<{ assignmentId: string }>();
  const { dashboard, api } = useConfig(['dashboard', 'api']);
  const { routes } = dashboard;

  const syncURL = useMemo(
    () =>
      replaceURLParams(routes.assignment_grades_sync, {
        assignment_id: assignmentId,
      }),
    [assignmentId, routes.assignment_grades_sync],
  );
  const updateSyncStatus = useCallback(
    (status: GradingSyncStatus) =>
      lastSync.data &&
      lastSync.mutate({
        ...lastSync.data,
        status,
      }),
    [lastSync],
  );

  const buttonContent = useMemo(() => {
    if (!studentsToSync || (lastSync.isLoading && !lastSync.data)) {
      return 'Loading...';
    }

    if (
      lastSync.data &&
      ['scheduled', 'in_progress'].includes(lastSync.data.status)
    ) {
      return (
        <>
          Syncing grades
          <SpinnerCircleIcon className="ml-1.5" />
        </>
      );
    }

    if (lastSync.data?.status === 'failed') {
      return (
        <>
          Error syncing. Click to retry
          <LeaveIcon />
        </>
      );
    }

    if (
      lastSync.error &&
      // The API returns 404 when current assignment has never been synced.
      // We can ignore those errors.
      (!(lastSync.error instanceof APIError) || lastSync.error.status !== 404)
    ) {
      return (
        <>
          Error checking sync status
          <LeaveIcon />
        </>
      );
    }

    if (studentsToSync.length > 0) {
      return `Sync ${studentsToSync.length} grades`;
    }

    return 'Grades synced';
  }, [studentsToSync, lastSync.isLoading, lastSync.data, lastSync.error]);

  const buttonDisabled =
    lastSync.isLoading ||
    lastSync.data?.status === 'scheduled' ||
    lastSync.data?.status === 'in_progress' ||
    !studentsToSync ||
    studentsToSync.length === 0;

  const syncGrades = useCallback(async () => {
    updateSyncStatus('scheduled');

    apiCall({
      authToken: api.authToken,
      path: syncURL,
      method: 'POST',
      data: {
        grades: studentsToSync,
      },
    })
      .then(() => onSyncScheduled())
      .catch(() => updateSyncStatus('failed'));
  }, [
    api.authToken,
    onSyncScheduled,
    studentsToSync,
    syncURL,
    updateSyncStatus,
  ]);

  return (
    <Button variant="primary" onClick={syncGrades} disabled={buttonDisabled}>
      {buttonContent}
    </Button>
  );
}
