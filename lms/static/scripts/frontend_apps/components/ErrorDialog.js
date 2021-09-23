import ErrorDisplay from './ErrorDisplay';
import Dialog from './Dialog';

/**
 * @typedef ErrorDialogProps
 * @prop {() => any} [onCancel]
 * @prop {string} [message] - Message to drill down to `ErrorDisplay`
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
  message = 'Error',
  error,
  cancelLabel,
}) {
  return (
    <Dialog
      role="alertdialog"
      title="Something went wrong"
      onCancel={onCancel}
      cancelLabel={cancelLabel}
    >
      <ErrorDisplay message={message} error={error} />
    </Dialog>
  );
}
