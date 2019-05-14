import { createElement } from 'preact';
import { useEffect, useRef } from 'preact/hooks';
import propTypes from 'prop-types';
import classNames from 'classnames';

import Button from './Button';
import { zIndexScale } from '../utils/style';

/**
 * Accessibility notes:
 *
 * Dialog accessibility is not trivial. We may want to use something like
 * https://github.com/reactjs/react-modal instead or as the basis of this
 * component.
 *
 * Resources:
 *
 * 1. https://developer.mozilla.org/en-US/docs/Web/Accessibility/ARIA/Roles/dialog_role
 * 2. https://developer.paciellogroup.com/blog/2018/06/the-current-state-of-modal-dialog-accessibility/
 * 3. https://www.marcozehe.de/2015/02/05/advanced-aria-tip-2-accessible-modal-dialogs/
 *
 * [3] is the most useful resource IMO as it highlights the essentials from
 * the perspective of a blind engineer.
 *
 * Things that are not implemented here yet:
 *
 * - A description which is reliably read out when the dialog is opened, in
 *   addition to the title.
 * - Saving and restoring keyboard focus when dialog is mounted and unmounted.
 * - Keeping tab focus within the dialog when shown.
 * - Hiding content underneath the dialog from screen readers.
 */

/**
 * A modal dialog with a title and a row of action buttons at the bottom.
 */
export default function Dialog({
  children,
  contentClass,
  initialFocus,
  onCancel,
  title,
  buttons,
}) {
  const handleKey = event => {
    event.stopPropagation();

    if (event.key === 'Escape' && typeof onCancel === 'function') {
      onCancel();
    }
  };

  const rootEl = useRef(null);
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
      role="dialog"
      aria-labelledby="Dialog__title"
      onKeyDown={handleKey}
      tabIndex="0"
      ref={rootEl}
    >
      <div
        className="Dialog__background"
        style={{ zIndex: zIndexScale.dialogBackground }}
      />
      <div className="Dialog__container" style={{ zIndex: zIndexScale.dialog }}>
        <div
          className={classNames({
            Dialog__content: true,
            [contentClass]: true,
          })}
        >
          <h1 className="Dialog__title" id="Dialog__title">
            {title}
            <span className="u-stretch" />
            <button className="Dialog__cancel-btn" onClick={onCancel}>
              ✕
            </button>
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
  children: propTypes.arrayOf(propTypes.element),

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
  buttons: propTypes.arrayOf(propTypes.element),

  /**
   * Class applied to the content of the dialog.
   *
   * The primary role of this class is to set the size of the dialog.
   */
  contentClass: propTypes.string,

  /** The title of the dialog. */
  title: propTypes.string,

  /**
   * A callback to invoke when the user cancels the dialog. If provided,
   * a "Cancel" button will be displayed.
   */
  onCancel: propTypes.func,
};
