// @ts-nocheck - TS doesn't understand `require('.../icon.svg')`

/**
 * Set of icons used by the LMS frontend via the `SvgIcon`
 * component.
 */
export default {
  // LMS icons
  'caret-down': require('../../images/caret-down.svg'),
  cancel: require('../../images/cancel.svg'),
  check: require('../../images/check.svg'),
  spinner: require('../../images/spinner.svg'),

  // Shared icons
  'arrow-left': require('@hypothesis/frontend-shared/images/icons/arrow-left.svg'),
  'arrow-right': require('@hypothesis/frontend-shared/images/icons/arrow-right.svg'),
};
