// @ts-nocheck - TS doesn't understand SVG imports.

// LMS icons
import caretDownIcon from '../../images/caret-down.svg';
import checkIcon from '../../images/check.svg';
import folderIcon from '../../images/folder.svg';
import pdfIcon from '../../images/file-pdf.svg';
import spinnerIcon from '../../images/spinner.svg';

// Shared icons
import arrowLeftIcon from '@hypothesis/frontend-shared/images/icons/arrow-left.svg';
import arrowRightIcon from '@hypothesis/frontend-shared/images/icons/arrow-right.svg';
import cancelIcon from '@hypothesis/frontend-shared/images/icons/cancel.svg';

/**
 * Set of icons used by the LMS frontend via the `SvgIcon` component.
 */
export default {
  // LMS icons
  'caret-down': caretDownIcon,
  check: checkIcon,
  folder: folderIcon,
  pdf: pdfIcon,
  spinner: spinnerIcon,

  // Shared icons
  'arrow-left': arrowLeftIcon,
  'arrow-right': arrowRightIcon,
  cancel: cancelIcon,
};
