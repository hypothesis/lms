import { createElement } from 'preact';
import propTypes from 'prop-types';

import Dialog from './Dialog';

/**
 * Wrapper around the Google Drive file picker dialog.
 */
export default function GoogleFilePicker({ onCancel }) {
  return (
    <Dialog onCancel={onCancel}>
      Google Drive file picker not yet implemented
    </Dialog>
  );
}

GoogleFilePicker.propTypes = {
  onCancel: propTypes.func,
};
