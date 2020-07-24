import { createElement } from 'preact';

import ErrorDisplay from './ErrorDisplay';
import Dialog from './Dialog';

/**
 * @typedef ErrorDialogProps
 * @prop {() => any} [onCancel]
 * @prop {string} title
 * @prop {import('./ErrorDisplay').ErrorLike} error
 */

/**
 * A dialog that informs the user about a problem that occurred and provides
 * them with links to get help or report the issue.
 *
 * @param {ErrorDialogProps} props
 */
export default function ErrorDialog({ onCancel, title, error }) {
  return (
    <Dialog
      role="alertdialog"
      title="Something went wrong :("
      onCancel={onCancel}
    >
      <ErrorDisplay message={title} error={error} />
    </Dialog>
  );
}
