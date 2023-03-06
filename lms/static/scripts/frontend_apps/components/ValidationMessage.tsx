import classnames from 'classnames';
import { useEffect, useState } from 'preact/hooks';

export type ValidationMessageProps = {
  /** Error message text. */
  message: string;

  /** Sets whether the message is visible. */
  open?: boolean;

  /** Callback invoked when message is closed. */
  onClose?: () => void;
};

/**
 * Shows a single validation error message. The user can dismiss the message
 * by clicking on it.
 */
export default function ValidationMessage({
  message,
  open = false,
  onClose = () => {},
}: ValidationMessageProps) {
  const [showError, setShowError] = useState(open);

  useEffect(() => {
    setShowError(open);
  }, [open]);

  const closeValidationError = (event: Event) => {
    event.preventDefault();
    setShowError(false);
    onClose();
  };

  return (
    <input
      type="button"
      data-testid={showError ? 'message-open' : 'message-closed'}
      onClick={closeValidationError}
      className={classnames(
        'absolute z-10 shadow',
        'text-white border-0 bg-red-error whitespace-nowrap overflow-hidden',
        // Narrow viewports position the message to the right of the input
        'left-full',
        // Sm and larger breakpoints position the message to the left of the input
        'sm:left-0 sm:-translate-x-full',
        'focus-visible-ring',
        // Make message the same height as its relative-positioned ancestor
        'h-full',
        {
          'animate-validationMessageOpen': showError,
          'animate-validationMessageClose': !showError,
        }
      )}
      value={message}
      tabIndex={showError ? 0 : -1}
    />
  );
}
