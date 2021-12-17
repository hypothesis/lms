import { LabeledButton, Modal } from '@hypothesis/frontend-shared';
import { useRef } from 'preact/hooks';

import ErrorDisplay from './ErrorDisplay';

/**
 * @typedef {import("@hypothesis/frontend-shared/lib/components/Modal").ModalProps} ModalProps
 * @typedef {import("preact").ComponentChildren} Children
 * @typedef {import('../errors').ErrorLike} ErrorLike
 */

/**
 * @typedef ErrorModalBaseProps
 * @prop {boolean} [busy] - Relevant when `onRetry` is provided. Indicates
 *   in-flight network or other activity and, when true, will disable the
 *   retry button.
 * @prop {Children} [children]
 * @prop {string} [cancelLabel="Close"] - The text displayed on the Modal's
 *   cancel button
 * @prop {string} [description] - A brief contextual description of the error
 *   state, which will be passed on to `ErrorDisplay`. Ignored if `error` is not
 *   present.
 * @prop {ErrorLike|null} [error] - When provided, `ErrorDetails` will be
 *   rendered, in addition to any `children`
 * @prop {() => void} [onRetry] - A callback for retrying the failed action.
 *   When present, a retry button will be rendered with any provided retry
 *   label.
 * @prop {string} [retryLabel="Try again"]
 * @prop {() => void} [onCancel] - A callback for closing/canceling the modal.
 *   If not provided, the modal will not be closeable.
 * @prop {string} [title="Something went wrong"]
 *
 */

/**
 * `ErrorModal` accepts and forwards on valid `ModalProps`. Required `Modal`
 * props that are re-declared as optional props (with defaults) in
 * `ErrorModalBaseProps` are omitted.
 *
 * @typedef {Omit<ModalProps, "cancelLabel"|"children"|"onCancel"|"title"> & ErrorModalBaseProps} ErrorModalProps
 *
 * */

/**
 * Render information about an error inside of a modal dialog, with optional
 * retry button.
 *
 * @param {ErrorModalProps} props
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
}) {
  const focusedDialogButton = /** @type {{ current: HTMLButtonElement }} */ (
    useRef()
  );
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
