import { isValidElement } from 'preact';

/**
 * Function that checks the prop `name` in `props` has an expected type or
 * throws otherwise.
 *
 * @typedef {(props: Object, name: string, component: string) => any} CheckPropFunction
 */

/**
 * Take a prop type checker function and return a checker where the prop is
 * optional. The optional checker has an `isRequired` property that requires the
 * prop.
 *
 * This matches how the standard prop types work (eg. `propTypes.object` is
 * optional, `propTypes.object.isRequired` is required).
 *
 * @param {CheckPropFunction} checkPropType
 * @return {CheckPropFunction}
 */
function checkOptionalProp(checkPropType) {
  const check = (props, propName, componentName) => {
    if (!(propName in props)) {
      return null;
    }
    return checkPropType(props, propName, componentName);
  };
  check.isRequired = checkPropType;
  return check;
}

/**
 * Check that a prop is a Preact element (ie. the result of a call to `createElement`
 * or a JSX element (`<div .../>`, `<Widget .../>`).
 *
 * This is the same as `propTypes.element`, but for Preact elements.
 *
 * @param {Object} props
 * @param {string} propName
 * @param {string} componentName
 */
function checkElementProp(props, propName, componentName) {
  if (!isValidElement(props[propName])) {
    return new Error(
      `Expected prop "${propName}" supplied to ${componentName} to be a Preact element`
    );
  }
  return null;
}

export const element = checkOptionalProp(checkElementProp);

/**
 * Check that a prop is a renderable value (ie. string, boolean, null or element)
 *
 * This is the same as `propTypes.node`, but for Preact nodes.
 *
 * @param {Object} props
 * @param {string} propName
 * @param {string} componentName
 */
function checkNodeProp(props, propName, componentName) {
  const value = props[propName];
  if (
    typeof value === 'string' ||
    typeof value === 'boolean' ||
    value === null ||
    isValidElement(value)
  ) {
    return null;
  }
  return new Error(
    `Expected prop "${propName}" supplied to ${componentName} to be a renderable value (string, boolean, element etc.)`
  );
}

export const node = checkOptionalProp(checkNodeProp);

/**
 * Patch `propTypes.{element, node}` to work with Preact (rather than React)
 * elements.
 *
 * @example
 *
 * ```
 * import propTypes from 'propTypes';
 * patchPropTypes(propTypes);
 * ```
 */
export function patchPropTypes(propTypes) {
  propTypes.element = element;
  propTypes.node = node;
}
