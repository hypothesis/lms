import { createElement, Fragment } from 'preact';
import propTypes from 'prop-types';

import SvgIcon from './SvgIcon';
import { trustMarkup } from '../utils/trusted';
/**
 * A spinning loading indicator.
 */
export default function Spinner({ className, hide }) {
  return (
    <Fragment>
      {!hide && (
        <SvgIcon
          className={className}
          src={trustMarkup(require('../../../images/spinner.svg'))}
          inline={true}
        />
      )}
    </Fragment>
  );
}

Spinner.propTypes = {
  className: propTypes.string,
  hide: propTypes.bool,
};
