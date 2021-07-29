// @ts-nocheck - TS doesn't understand `require('.../icon.svg')`

/**
 * Set of icons used by the LMS frontend via the `SvgIcon`
 * component.
 */
export default {
  // LMS icons
  'caret-down': require('../../images/caret-down.svg'),
  check: require('../../images/check.svg'),
  folder: require('../../images/folder.svg'),
  pdf: require('../../images/file-pdf.svg'),
  spinner: require('../../images/spinner.svg'),

  // Shared icons
  'arrow-left': require('@hypothesis/frontend-shared/images/icons/arrow-left.svg'),
  'arrow-right': require('@hypothesis/frontend-shared/images/icons/arrow-right.svg'),
  cancel: require('@hypothesis/frontend-shared/images/icons/cancel.svg'),
};
