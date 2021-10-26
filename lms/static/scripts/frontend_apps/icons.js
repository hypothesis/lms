// @ts-nocheck - TS doesn't understand SVG imports.

// LMS icons
// TODO: replace these with shared versions when updating the file picker:
// https://github.com/hypothesis/lms/issues/3189
import folderIcon from '../../images/folder.svg';
import pdfIcon from '../../images/file-pdf.svg';

// TODO: Remove when `frontend-shared` provides a FullScreenSpinner component
import spinnerIcon from '../../images/spinner.svg';

// Shared icons
import {
  arrowLeft,
  arrowRight,
  cancel,
  caretDown,
  check,
} from '@hypothesis/frontend-shared/lib/icons';

export default {
  // LMS icons
  folder: folderIcon,
  pdf: pdfIcon,
  spinner: spinnerIcon,

  // Shared icons
  'arrow-left': arrowLeft,
  'arrow-right': arrowRight,
  cancel,
  'caret-down': caretDown,
  check,
};
