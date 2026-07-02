import { formatDateTime } from '@hypothesis/frontend-shared';

import type { CheckpointConfig } from '../config';
import RevealAnnotationsButton from './RevealAnnotationsButton';

export default function CheckpointBar({
  checkpoint,
  dueDate,
}: {
  checkpoint: CheckpointConfig;
  dueDate?: string | null;
}) {
  return (
    <div className="p-2 border-t grid grid-cols-1 gap-2 items-center text-center md:text-left md:grid-cols-[auto_1fr_auto]">
      <div className="text-sm" data-testid="checkpoint-type">
        <div className="font-semibold">Checkpoint:</div>
        <div>Manual</div>
      </div>
      {dueDate && (
        <div className="text-sm md:text-center" data-testid="checkpoint-due-date">
          <div className="font-semibold">Due Date:</div>
          <div>{formatDateTime(dueDate)}</div>
        </div>
      )}
      <div className="flex justify-center md:justify-end">
        <RevealAnnotationsButton checkpoint={checkpoint} />
      </div>
    </div>
  );
}
