import classNames from 'classnames';
import propTypes from 'prop-types';
import { createElement } from 'preact';

/**
 * @typedef ButtonProps
 * @prop {string} [className]
 * @prop {boolean} [disabled]
 * @prop {string} label
 * @prop {() => any} onClick
 * @prop {string} [type]
 */

/**
 * @param {ButtonProps} props
 */
export default function Button({
  className = '',
  disabled = false,
  label,
  onClick,
  type = 'button',
}) {
  return (
    <button
      className={classNames({ Button: true, [className]: true })}
      disabled={disabled}
      onClick={onClick}
      type={type}
    >
      {label}
    </button>
  );
}

Button.propTypes = {
  className: propTypes.string,
  disabled: propTypes.bool,
  label: propTypes.string,
  onClick: propTypes.func,
  type: propTypes.string,
};
