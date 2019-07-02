import { createElement } from 'preact';
import propTypes from 'prop-types';

import ErrorDisplay from './ErrorDisplay';
import Dialog from './Dialog';

/**
 * A dialog that informs the user about a problem that occurred and provides
 * them with links to get help or report the issue.
 */
export default function ErrorDialog({ onCancel, title, error }) {
  return (
    <Dialog title="Something went wrong :(" onCancel={onCancel}>
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
};
