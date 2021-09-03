import { SvgIcon } from '@hypothesis/frontend-shared';

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
