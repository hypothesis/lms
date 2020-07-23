import { createElement } from 'preact';
import { useEffect, useRef } from 'preact/hooks';
import classNames from 'classnames';

import Button from './Button';
import useElementShouldClose from '../common/use-element-should-close';
import { zIndexScale } from '../utils/style';
import { useUniqueId } from '../utils/hooks';

/**
 * @typedef {import("preact").JSX.Element} JSXElement
 *
 * @typedef DialogProps
 * @prop {Object} children - The content of the dialog.
 * @prop {import("preact/hooks").Ref<HTMLElement>} [initialFocus] -
 *   Child element to focus when the dialog is rendered.
 * @prop {JSXElement[]} [buttons] -
 *   Additional `Button` elements to display at the bottom of the dialog.
 *   A "Cancel" button is added automatically if the `onCancel` prop is set.
 * @prop {string} [contentClass] - e.g. <button>
 * @prop {'dialog'|'alertdialog'} [role] - The aria role for the dialog (defaults to" dialog")
 * @prop {string} title - The title of the dialog.
 * @prop {() => any} [onCancel] -
 *   A callback to invoke when the user cancels the dialog. If provided, a
 *   "Cancel" button will be displayed.
 */

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
 *
 * @param {DialogProps} props
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
  const dialogTitleId = useUniqueId('dialog-title');
  const dialogDescriptionId = useUniqueId('dialog-description');
  const rootEl = useRef(/** @type {HTMLDivElement | null} */ (null));

  useElementShouldClose(rootEl, true, () => {
    if (onCancel) {
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
    <div>
      <div
        className="Dialog__background"
        style={{ zIndex: zIndexScale.dialogBackground }}
      />
      <div className="Dialog__container" style={{ zIndex: zIndexScale.dialog }}>
        <div
          tabIndex={-1}
          ref={rootEl}
          role={role}
          aria-labelledby={dialogTitleId}
          aria-describedby={dialogDescriptionId}
          aria-modal={true}
          className={classNames('Dialog__content', contentClass)}
        >
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
          <div id={dialogDescriptionId}>{children}</div>
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
