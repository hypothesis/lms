import {
  Button,
  ModalDialog,
  formatDateTime,
} from '@hypothesis/frontend-shared';
import { useCallback, useRef, useState } from 'preact/hooks';

import type { CheckpointConfig } from '../config';
import { useConfig } from '../config';
import { apiCall } from '../utils/api';
import ErrorDisplay from './ErrorDisplay';

export type RevealAnnotationsButtonProps = {
  checkpoint: CheckpointConfig;
};

/**
 * Button and confirmation modal for revealing checkpoint annotations.
 * When the instructor clicks "Reveal annotations", a confirmation modal warns
 * that this action cannot be undone. On confirm, it calls the reveal API and
 * updates the local state.
 */
export default function RevealAnnotationsButton({
  checkpoint,
}: RevealAnnotationsButtonProps) {
  const {
    api: { authToken },
  } = useConfig(['api']);

  const [showModal, setShowModal] = useState(false);
  const [revealed, setRevealed] = useState(checkpoint.revealed);
  const [revealDate, setRevealDate] = useState<string | null>(
    checkpoint.revealDate,
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const revealButtonRef = useRef<HTMLButtonElement | null>(null);

  const handleReveal = useCallback(async () => {
    setBusy(true);
    setError(null);
    try {
      const result = await apiCall<{ reveal_date: string }>({
        authToken,
        path: checkpoint.revealUrl,
        data: {},
      });
      setRevealed(true);
      setRevealDate(result.reveal_date);
      setShowModal(false);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  }, [authToken, checkpoint.revealUrl]);

  if (revealed) {
    return (
      <span
        className="text-sm text-color-text-light italic"
        data-testid="checkpoint-revealed"
      >
        Annotations revealed on
        <br className="md:hidden" />
        {' '}
        {revealDate ? formatDateTime(revealDate) : ''}
      </span>
    );
  }

  return (
    <>
      <Button
        onClick={() => setShowModal(true)}
        data-testid="reveal-annotations-button"
      >
        Reveal annotations
      </Button>

      {showModal && (
        <ModalDialog
          title="This action cannot be undone"
          onClose={() => setShowModal(false)}
          initialFocus={revealButtonRef}
          buttons={
            <Button
              elementRef={revealButtonRef}
              variant="primary"
              onClick={handleReveal}
              disabled={busy}
              data-testid="confirm-reveal-button"
            >
              Reveal
            </Button>
          }
        >
          <p className="text-sm">
            Student annotations and instructor replies that are currently hidden
            will be revealed and cannot be hidden again.
          </p>
          {error && (
            <ErrorDisplay
              classes="pt-4"
              description="Failed to reveal annotations"
              error={error}
            />
          )}
        </ModalDialog>
      )}
    </>
  );
}
