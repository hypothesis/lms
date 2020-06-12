import { createElement } from 'preact';
import classnames from 'classnames';
import propTypes from 'prop-types';

import SvgIcon from './SvgIcon';
import { trustMarkup } from '../utils/trusted';

/**
 * A spinning loading indicator.
 */
export default function Spinner({ className, visible = false }) {
  return (
    <span
      className={classnames('Spinner', className, {
        'Spinner--fade-in': visible,
      })}
    >
      <SvgIcon
        className={'Spinner__svg'}
        src={trustMarkup(require('../../../images/spinner.svg'))}
      />
    </span>
  );
}

Spinner.propTypes = {
  /**
   * A CSS class to apply to wrapper element. this can be used for
   * positioning, and optionally color and size.
   */
  className: propTypes.string,
  /**
   * Shows the spinner when true and hides it otherwise.
   * Applies a css fade animate when this variable is toggle.
   */
  visible: propTypes.bool,
};
