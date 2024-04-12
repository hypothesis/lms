import { Button, ModalDialog } from '@hypothesis/frontend-shared';
import type { PanelModalDialogProps } from '@hypothesis/frontend-shared/lib/components/feedback/ModalDialog';
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

  /**
   * Wether or not to show the standard link to our support page
   */
  displaySupportLink?: boolean;
};

/** `title` is optional for this component but required by `Modal` */
export type ErrorModalProps = Omit<PanelModalDialogProps, 'title'> &
  ErrorModalBaseProps;

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
  displaySupportLink = true,

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
    <ModalDialog
      buttons={buttons}
      initialFocus={focusedDialogButton}
      onClose={onCancel}
      role="alertdialog"
      title={title}
      {...restProps}
    >
      {error && (
        <ErrorDisplay
          description={description}
          error={error}
          displaySupportLink={displaySupportLink}
        >
          {children}
        </ErrorDisplay>
      )}
      {!error && children}
    </ModalDialog>
  );
}
