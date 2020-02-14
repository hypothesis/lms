import { createElement } from 'preact';
import { useEffect, useState } from 'preact/hooks';
import classNames from 'classnames';
import propTypes from 'prop-types';

/**
 * Shows a single validation error message that can be open or closed.
 * A user can also close the message by clicking on it.
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
   */
  const closeValidationError = () => {
    setShowError(false);
    onClose();
  };

  const errorClass = classNames('ValidationMessage', {
    'ValidationMessage--open': showError,
    'ValidationMessage--closed': !showError,
  });

  return (
    // FIXME-A11Y
    // eslint-disable-next-line jsx-a11y/no-static-element-interactions, jsx-a11y/click-events-have-key-events
    <div onClick={closeValidationError} className={errorClass}>
      {message}
    </div>
  );
}

ValidationMessage.propTypes = {
  // Error message text
  message: propTypes.string.isRequired,
  // Should this be open or closed
  open: propTypes.bool,
  // Optional callback when the error message closes itself via onClick
  onClose: propTypes.func,
};
