import { createElement } from 'preact';
import propTypes from 'prop-types';

/**
 * A spinning loading indicator.
 */
export default function Spinner({ className }) {
  return <img className={className} src="/static/images/spinner.svg" />;
}

Spinner.propTypes = {
  className: propTypes.string,
};
