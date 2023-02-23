import { Button, Modal } from '@hypothesis/frontend-shared/lib/next';
import type { ModalProps } from '@hypothesis/frontend-shared/lib/components/feedback/Modal';
import type { ComponentChildren } from 'preact';
import { useRef } from 'preact/hooks';

import type { ErrorLike } from '../errors';
import ErrorDisplay from './ErrorDisplay';

type ErrorModalBaseProps = {
  /**
   * When `true`, disables the retry button. Only relevant when `onRetry` is
   * provided.
   */
  busy?: boolean;
  children?: ComponentChildren;
  /**
   * Text displayed on the Modal's cancel button. Only relevant when `onCancel`
   * is provided.
   */
  cancelLabel?: string;

  /**
   * A brief contextual description of the error state, which will be passed on
   * to `ErrorDisplay`. Ignored if `error` is not present.
   */
  description?: string;

  /**
   * When provided, `ErrorDetails` will be rendered, in addition to any
   * `children`
   */
  error?: ErrorLike | null;

  /**
   * A callback for retrying the failed action. When present, a retry button
   * will be rendered.
   */
  onRetry?: () => void;
  /** Text for retry button, if present. */
  retryLabel?: string;

  /**
   * A callback for closing/canceling the modal. If not provided, the modal
   * will not be closeable.
   */
  onCancel?: () => void;
  title?: string;
};

/** `title` is optional for this component but required by `Modal` */
export type ErrorModalProps = Omit<ModalProps, 'title'> & ErrorModalBaseProps;

/**
 * Render information about an error inside of a modal dialog, with optional
 * retry button.
 */
export default function ErrorModal({
  busy,
  cancelLabel = 'Close',
  children,
  description,
  error,
  onCancel,
  onRetry,
  retryLabel = 'Try again',

  // Modal props
  title = 'Something went wrong',

  // Other props to forward on to Modal
  ...restProps
}: ErrorModalProps) {
  const focusedDialogButton = useRef<HTMLButtonElement | null>(null);
  const buttons = (
    <>
      {onCancel && (
        <Button data-testid="cancel-button" onClick={onCancel}>
          {cancelLabel}
        </Button>
      )}
      {onRetry && (
        <Button
          elementRef={focusedDialogButton}
          data-testid="retry-button"
          disabled={busy}
          onClick={onRetry}
          variant="primary"
        >
          {retryLabel}
        </Button>
      )}
    </>
  );
  return (
    <Modal
      buttons={buttons}
      initialFocus={focusedDialogButton}
      onClose={onCancel}
      role="alertdialog"
      title={title}
      {...restProps}
    >
      {error && (
        <ErrorDisplay description={description} error={error}>
          {children}
        </ErrorDisplay>
      )}
      {!error && children}
    </Modal>
  );
}
