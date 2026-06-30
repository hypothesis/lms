import { formatDateTime } from '@hypothesis/frontend-shared';

import { useConfig } from '../config';

type SyncCheckpoint = {
  revealed: boolean;
  revealDate: string | null;
};

export default function StudentCheckpointBar({
  syncCheckpoint,
}: {
  syncCheckpoint?: SyncCheckpoint | null;
}) {
  // checkpoint comes from the initial JS config set during _show_document.
  // For course-grouping assignments, this has the real state from h and is
  // the only source (there is no client-side sync).
  // For section/group assignments, this is a default (hidden: true) and
  // syncCheckpoint will override it with the real state from h.
  const { studentCheckpoint: checkpoint } = useConfig();
  if (!checkpoint) {
    return null;
  }

  const hidden = syncCheckpoint ? !syncCheckpoint.revealed : checkpoint.hidden;

  return (
    <header className="p-2 flex items-center">
      <div className="text-sm" data-testid="student-checkpoint-status">
        <div className="font-semibold">Checkpoint:</div>
        <div>
          {hidden ? 'Annotations are hidden' : 'Annotations are visible'}
        </div>
      </div>
      {checkpoint.dueDate && (
        <div
          className="text-sm ml-auto"
          data-testid="student-checkpoint-due-date"
        >
          <div className="font-semibold">Assignment Due Date:</div>
          <div>{formatDateTime(checkpoint.dueDate)}</div>
        </div>
      )}
    </header>
  );
}
