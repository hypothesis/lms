import { formatDateTime } from '@hypothesis/frontend-shared';

import { useConfig } from '../config';

export default function StudentCheckpointBar() {
  const { studentCheckpoint } = useConfig();
  if (!studentCheckpoint) {
    return null;
  }

  return (
    <header className="p-2 flex items-center">
      <div className="text-sm" data-testid="student-checkpoint-status">
        <div className="font-semibold">Checkpoint:</div>
        <div>{studentCheckpoint.hidden ? 'Annotations are hidden' : 'Annotations are visible'}</div>
      </div>
      {studentCheckpoint.dueDate && (
        <div className="text-sm ml-auto" data-testid="student-checkpoint-due-date">
          <div className="font-semibold">Assignment Due Date:</div>
          <div>{formatDateTime(studentCheckpoint.dueDate)}</div>
        </div>
      )}
    </header>
  );
}
