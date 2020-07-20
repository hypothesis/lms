import { createElement } from 'preact';
import propTypes from 'prop-types';

import SvgIcon from './SvgIcon';

/**
 * @typedef SpinnerProps
 * @prop {string} [className] - Additional classes to add to the spinner
 */

/**
 * A spinning loading indicator.
 *
 * @param {SpinnerProps} props
 */
export default function Spinner({ className }) {
  return <SvgIcon className={className} name="spinner" inline={true} />;
}

Spinner.propTypes = {
  className: propTypes.string,
};
