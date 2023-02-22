import { LabeledButton, Modal } from '@hypothesis/frontend-shared';
import type { ModalProps } from '@hypothesis/frontend-shared/lib/components/Modal';
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
  /** Text displayed on the Modal's cancel button */
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

export type ErrorModalProps = Omit<
  ModalProps,
  'cancelLabel' | 'children' | 'onCancel' | 'title'
> &
  ErrorModalBaseProps;

/**
 * Render information about an error inside of a modal dialog, with optional
 * retry button.
 */
export default function ErrorModal({
  busy,
  children,
  description,
  error,
  onRetry,
  retryLabel = 'Try again',

  // Modal props
  cancelLabel = 'Close',
  onCancel,
  title = 'Something went wrong',

  // Other props to forward on to Modal
  ...restProps
}: ErrorModalProps) {
  const focusedDialogButton = useRef<HTMLButtonElement | null>(null);
  const buttons = onRetry && (
    <LabeledButton
      buttonRef={focusedDialogButton}
      data-testid="retry-button"
      disabled={busy}
      onClick={onRetry}
      variant="primary"
    >
      {retryLabel}
    </LabeledButton>
  );
  return (
    <Modal
      buttons={buttons}
      cancelLabel={cancelLabel}
      contentClass="LMS-Dialog LMS-Dialog--medium"
      initialFocus={focusedDialogButton}
      onCancel={onCancel ?? (() => null)}
      role="alertdialog"
      title={title}
      withCancelButton={!!onCancel}
      withCloseButton={!!onCancel}
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
