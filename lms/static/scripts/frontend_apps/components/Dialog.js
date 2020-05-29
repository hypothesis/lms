import { createElement } from 'preact';
import { useEffect, useRef } from 'preact/hooks';
import propTypes from 'prop-types';
import classNames from 'classnames';

import Button from './Button';
import useElementShouldClose from '../common/use-element-should-close';
import { zIndexScale } from '../utils/style';
import { useUniqueId } from '../utils/hooks';

/**
 * A modal dialog wrapper with a title. The wrapper sets initial focus to itself
 * unless an element inside of it is specified with the `initialFocus` ref.
 * Optional action buttons may be passed in with the `buttons` prop but the
 * cancel button is automatically generated when the on `onCancel` function is
 * passed.
 *
 * Canonical resources:
 *
 * https://www.w3.org/TR/wai-aria-practices/examples/dialog-modal/dialog.html
 * https://www.w3.org/TR/wai-aria-practices/examples/dialog-modal/alertdialog.html
 *
 * Things that are not implemented here yet:
 *
 * - A description which is reliably read out when the dialog is opened, in
 *   addition to the title.
 */
export default function Dialog({
  children,
  contentClass,
  initialFocus,
  onCancel,
  role = 'dialog',
  title,
  buttons,
}) {
  const dialogTitleId = useUniqueId('dialog');
  const rootEl = useRef();

  useElementShouldClose(rootEl, true, () => {
    if (typeof onCancel === 'function') {
      onCancel();
    }
  });

  useEffect(() => {
    if (initialFocus) {
      initialFocus.current.focus();
    } else {
      // Modern accessibility guidance is to focus the dialog itself rather than
      // trying to be smart about focusing a particular control within the
      // dialog. See resources above.
      rootEl.current.focus();
    }
    // We only want to run this effect once when the dialog is mounted.
    //
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div
      role={role}
      aria-labelledby={dialogTitleId}
      aria-modal="true"
      ref={rootEl}
      tabIndex="-1"
    >
      <div
        className="Dialog__background"
        style={{ zIndex: zIndexScale.dialogBackground }}
      />
      <div className="Dialog__container" style={{ zIndex: zIndexScale.dialog }}>
        <div className={classNames('Dialog__content', contentClass)}>
          <h1 className="Dialog__title" id={dialogTitleId}>
            {title}
            <span className="u-stretch" />
            {onCancel && (
              <button
                aria-label="Close"
                className="Dialog__cancel-btn"
                onClick={onCancel}
              >
                ✕
              </button>
            )}
          </h1>
          {children}
          <div className="u-stretch" />
          <div className="Dialog__actions">
            {onCancel && (
              <Button
                className="Button--cancel"
                onClick={onCancel}
                label="Cancel"
              />
            )}
            {buttons}
          </div>
        </div>
      </div>
    </div>
  );
}

Dialog.propTypes = {
  /** The content of the dialog. */
  children: propTypes.any,

  /**
   * A ref associated with the child element to focus when the dialog is
   * rendered.
   */
  initialFocus: propTypes.object,

  /**
   * Additional buttons to display at the bottom of the dialog.
   *
   * The "Cancel" button is added automatically if the `onCancel` prop is set.
   */
  buttons: propTypes.arrayOf(
    propTypes.oneOfType([propTypes.instanceOf(Button), propTypes.element])
  ), // e.g. <button>

  /**
   * Class applied to the content of the dialog.
   *
   * The primary role of this class is to set the size of the dialog.
   */
  contentClass: propTypes.string,

  /**
   * The aria role for the dialog (defaults to" dialog")
   */
  role: propTypes.oneOf(['alertdialog', 'dialog']),

  /** The title of the dialog. */
  title: propTypes.string,

  /**
   * A callback to invoke when the user cancels the dialog. If provided,
   * a "Cancel" button will be displayed.
   */
  onCancel: propTypes.func,
};
