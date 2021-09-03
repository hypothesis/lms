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

  const errorClass = classNames('ValidationMessage', {
    'ValidationMessage--open': showError,
    'ValidationMessage--closed': !showError,
  });

  return (
    <input
      type="button"
      onClick={closeValidationError}
      className={errorClass}
      value={message}
      tabIndex={showError ? 0 : -1}
    />
  );
}
