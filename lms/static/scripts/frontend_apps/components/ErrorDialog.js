import { Modal } from '@hypothesis/frontend-shared';

import ErrorDisplay from './ErrorDisplay';

/**
 * @typedef ErrorDialogProps
 * @prop {() => any} onCancel
 * @prop {string} [description] - Message to drill down to `ErrorDisplay`
 * @prop {import('./ErrorDisplay').ErrorLike} error
 * @prop {string} [cancelLabel]
 */

/**
 * A dialog that informs the user about a problem that occurred and provides
 * them with links to get help or report the issue.
 *
 * @param {ErrorDialogProps} props
 */
export default function ErrorDialog({
  onCancel,
  description,
  error,
  cancelLabel,
}) {
  return (
    <Modal
      cancelLabel={cancelLabel}
      contentClass="LMS-Dialog LMS-Dialog--medium"
      onCancel={onCancel}
      role="alertdialog"
      title="Something went wrong"
    >
      <ErrorDisplay description={description} error={error} />
    </Modal>
  );
}
