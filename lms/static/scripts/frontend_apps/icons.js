// @ts-nocheck - TS doesn't understand SVG imports.

// TODO: Remove when `frontend-shared` provides a FullScreenSpinner component
import spinnerIcon from '../../images/spinner.svg';

import {
  arrowLeft,
  arrowRight,
  cancel,
  caretDown,
  check,
  filePDFFilled,
  folder,
} from '@hypothesis/frontend-shared/lib/icons';

export default {
  // LMS local icons
  spinner: spinnerIcon,

  // Shared icons
  'arrow-left': arrowLeft,
  'arrow-right': arrowRight,
  cancel,
  'caret-down': caretDown,
  check,
  folder,
  pdf: filePDFFilled,
};
