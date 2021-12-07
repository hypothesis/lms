import { useEffect, useState } from 'preact/hooks';
import classNames from 'classnames';

/**
 * @typedef ValidationMessageProps
 * @prop {string} message - Error message text
 * @prop {boolean} [open] - Should this be open or closed
 * @prop {() => any} [onClose] - Optional callback when the error message is closed
 */

/**
 * Shows a single validation error message that can be open or closed.
 * A user can also close the message by clicking on it.
 *
 * @param {ValidationMessageProps} props
 */
export default function ValidationMessage({
  message,
  open = false,
  onClose = () => {},
}) {
  const [showError, setShowError] = useState(open);

  useEffect(() => {
    setShowError(open);
  }, [open]);

  /**
   * Closes the validation error message and notifies parent
   *
   * @param {Event} event
   */
  const closeValidationError = event => {
    event.preventDefault();
    setShowError(false);
    onClose();
  };

  return (
    <input
      type="button"
      data-testid={showError ? 'message-open' : 'message-closed'}
      onClick={closeValidationError}
      className={classNames(
        'absolute z-10 h-touch-minimum shadow',
        'text-white border-0 bg-error whitespace-nowrap overflow-hidden',
        // Narrow viewports position the message to the right of the input
        'left-full',
        // Sm and larger breakpoints position the message to the left of the input
        'sm:left-0 sm:-translate-x-full',
        'hyp-u-outline-on-keyboard-focus',
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
