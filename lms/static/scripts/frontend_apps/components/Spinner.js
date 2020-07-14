import { createElement } from 'preact';
import propTypes from 'prop-types';

import SvgIcon from './SvgIcon';

/**
 * A spinning loading indicator.
 */
export default function Spinner({ className }) {
  return <SvgIcon className={className} name="spinner" inline={true} />;
}

Spinner.propTypes = {
  className: propTypes.string,
};
