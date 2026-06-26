import { formatDateTime } from '@hypothesis/frontend-shared';

import type { CheckpointConfig } from '../config';
import RevealAnnotationsButton from './RevealAnnotationsButton';

export default function CheckpointBar({
  checkpoint,
}: {
  checkpoint: CheckpointConfig;
}) {
  return (
    <div className="p-2 flex items-center border-t">
      <div className="text-sm" data-testid="checkpoint-type">
        <div className="font-semibold">Checkpoint:</div>
        <div>Manual</div>
      </div>
      {checkpoint.dueDate && (
        <div className="text-sm mx-auto" data-testid="checkpoint-due-date">
          <div className="font-semibold">Due Date:</div>
          <div>{formatDateTime(checkpoint.dueDate)}</div>
        </div>
      )}
      <div className="ml-auto">
        <RevealAnnotationsButton checkpoint={checkpoint} />
      </div>
    </div>
  );
}
