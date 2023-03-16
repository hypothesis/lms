import type { ModalProps } from '@hypothesis/frontend-shared/lib/components/feedback/Modal';
import { Button, Modal } from '@hypothesis/frontend-shared/lib/next';
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

  /**
   * Content of the dialog. This should be a human-readable explanation of the
   * problem that occurred and may include hints on how to fix it.
   */
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
   * Additional actions that will be displayed in the footer of the dialog.
   */
  extraActions?: ComponentChildren;

  /**
   * A callback for closing/canceling the modal. If not provided, the modal
   * will not be closeable.
   */
  onCancel?: () => void;

  /**
   * A callback for retrying the failed action. When present, a retry button
   * will be rendered.
   */
  onRetry?: () => void;

  /** Text for retry button, if present. */
  retryLabel?: string;

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
  extraActions,
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
      {extraActions}
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
