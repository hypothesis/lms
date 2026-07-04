import { formatDateTime } from '@hypothesis/frontend-shared';

import { useConfig } from '../config';

type SyncCheckpoint = {
  revealed: boolean;
  revealDate: string | null;
};

export default function StudentToolbar({
  syncCheckpoint,
  waitingForSync,
}: {
  syncCheckpoint?: SyncCheckpoint | null;
  waitingForSync?: boolean;
}) {
  const { studentToolbar } = useConfig();
  if (!studentToolbar?.assignmentCheckpointEnabled) {
    return null;
  }

  if (waitingForSync) {
    return null;
  }

  const courseCheckpointConfig = studentToolbar.courseCheckpointConfig;

  const revealed = syncCheckpoint
    ? syncCheckpoint.revealed
    : courseCheckpointConfig?.revealed ?? false;

  return (
    <header className="p-2 grid grid-cols-1 gap-2 items-center text-center md:text-left md:grid-cols-[auto_1fr]">
      <div className="text-sm" data-testid="student-checkpoint-status">
        <div className="font-semibold">Checkpoint:</div>
        <div>
          {revealed ? 'Annotations are visible' : 'Annotations are hidden'}
        </div>
      </div>
      {studentToolbar.assignmentDueDate && (
        <div
          className="text-sm md:text-right"
          data-testid="student-checkpoint-due-date"
        >
          <div className="font-semibold">Assignment Due Date:</div>
          <div>{formatDateTime(studentToolbar.assignmentDueDate)}</div>
        </div>
      )}
    </header>
  );
}
