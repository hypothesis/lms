import { createElement } from 'preact';
import propTypes from 'prop-types';

import ErrorDisplay from './ErrorDisplay';
import Dialog from './Dialog';

/**
 * A dialog that informs the user about a problem that occurred and provides
 * them with links to get help or report the issue.
 */
export default function ErrorDialog({ onCancel, title, error, size = {} }) {
  return (
    <Dialog
      role="alertdialog"
      title="Something went wrong :("
      onCancel={onCancel}
      size={size}
    >
      <ErrorDisplay message={title} error={error} />
    </Dialog>
  );
}

ErrorDialog.propTypes = {
  onCancel: propTypes.func,
  title: propTypes.string.isRequired,
  error: propTypes.shape({
    message: propTypes.string.isRequired,
  }),
  /**
   * Pass a width and/or height value to the child Dialog
   */
  size: propTypes.shape({
    height: propTypes.oneOfType([propTypes.string, propTypes.number]),
    width: propTypes.oneOfType([propTypes.string, propTypes.number]),
  }),
};
