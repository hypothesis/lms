import { Button, LeaveIcon } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useCallback, useMemo, useState } from 'preact/hooks';
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

  const syncedStudentsCount = useMemo(
    () =>
      lastSync.data?.grades.filter(s => s.status !== 'in_progress').length ?? 0,
    [lastSync.data?.grades],
  );
  const [totalStudentsToSync, setTotalStudentsToSync] = useState<number>();
  const startSync = useCallback(() => {
    // Right before starting, set amount of students that are going to be synced.
    // This will prevent displaying a zero in the short interval between the
    // list of students to sync is cleared, and the next sync check happens
    setTotalStudentsToSync(studentsToSync?.length ?? 0);
    updateSyncStatus('scheduled');
  }, [studentsToSync?.length, updateSyncStatus]);

  const buttonContent = useMemo(() => {
    if (!studentsToSync || (lastSync.isLoading && !lastSync.data)) {
      return 'Loading...';
    }

    if (
      lastSync.data &&
      ['scheduled', 'in_progress'].includes(lastSync.data.status)
    ) {
      // Use the amount set when a sync is started, but fall back to the amount
      // of students from last sync, in case a sync was in progress when this
      // was loaded
      const totalStudentsBeingSynced =
        totalStudentsToSync ?? lastSync.data.grades.length;

      return (
        <>
          Syncing grades
          <div
            className={classnames(
              'border-solid border-l border-grey-5',
              // Compensate the Button's padding, so that this "separator"
              // covers the entire height of the Button
              '-my-2 self-stretch',
            )}
          />
          <div className="text-grey-3 text-[0.7rem] self-center">
            {syncedStudentsCount}/{totalStudentsBeingSynced}
          </div>
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
  }, [
    studentsToSync,
    lastSync.isLoading,
    lastSync.data,
    lastSync.error,
    totalStudentsToSync,
    syncedStudentsCount,
  ]);

  const buttonDisabled =
    lastSync.isLoading ||
    lastSync.data?.status === 'scheduled' ||
    lastSync.data?.status === 'in_progress' ||
    !studentsToSync ||
    studentsToSync.length === 0;

  const syncGrades = useCallback(() => {
    startSync();

    return apiCall({
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
    startSync,
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
