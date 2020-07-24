/**
 * Return true if `value` "looks like" a React/Preact component.
 */
function isComponent(value) {
  return (
    typeof value === 'function' &&
    value.name.match(/^[A-Z]/) &&
    // A crude test to check that the function returns a JSX expression.
    //
    // This won't work if the component is an arrow function, or if `createElement`
    // is imported under a different name.
    value.toString().match(/\breturn\b.*\bcreateElement\b/)
  );
}

/**
 * Return the display name of a component, minus the names of any wrappers
 * (eg. `withServices(OriginalName)` becomes `OriginalName`).
 *
 * @param {Function} component - A Preact component
 * @return {string}
 */
function getDisplayName(component) {
  let displayName =
    component.displayName || component.name || 'UnknownComponent';

  const wrappedComponentMatch = displayName.match(/\([A-Z][A-Za-z0-9]+\)/);
  if (wrappedComponentMatch) {
    displayName = wrappedComponentMatch[0].slice(1, -1);
  }

  return displayName;
}

/**
 * Helper for use with `babel-plugin-mockable-imports` that mocks components
 * imported by a file.
 *
 * Mocked components will have the same display name as the original component,
 * minus any wrappers (eg. `Widget` and `withServices(Widget)` both become
 * `Widget`). They will render only their children, as if they were just a
 * `Fragment`.
 *
 * @example
 *   beforeEach(() => {
 *     ComponentUnderTest.$imports.$mock(mockImportedComponents());
 *
 *     // Add additional mocks or overrides here.
 *   });
 *
 *   afterEach(() => {
 *     ComponentUnderTest.$imports.$restore();
 *   });
 *
 * @return {Function} - A function that can be passed to `$imports.$mock`.
 */
export default function mockImportedComponents() {
  return (source, symbol, value) => {
    if (!isComponent(value)) {
      return null;
    }

    const mock = props => props.children;
    mock.displayName = getDisplayName(value);

    return mock;
  };
}
