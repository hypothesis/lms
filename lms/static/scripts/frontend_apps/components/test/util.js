/**
 * Wrapper returned by `mount` or `shallow` Enzyme functions.
 *
 * @typedef {import("enzyme").CommonWrapper} CommonWrapper
 */

/**
 * Default timeout used by `waitFor*` functions.
 */
const DEFAULT_TIMEOUT = 100;

/**
 * Wait for a condition to evaluate to a truthy value.
 *
 * @param {() => any} condition - Function that returns a truthy value when some condition is met
 * @param {number} timeout - Max delay in milliseconds to wait
 * @param {string} what - Description of condition that is being waited for
 * @return {Promise<any>} - Result of the `condition` function
 */
export async function waitFor(
  condition,
  timeout = DEFAULT_TIMEOUT,
  what = condition.toString()
) {
  const result = condition();
  if (result) {
    return result;
  }

  const start = Date.now();

  return new Promise((resolve, reject) => {
    const timer = setInterval(() => {
      const result = condition();
      if (result) {
        clearTimeout(timer);
        resolve(result);
      }
      if (Date.now() - start > timeout) {
        clearTimeout(timer);
        reject(new Error(`waitFor(${what}) failed after ${timeout} ms`));
      }
    });
  });
}

/**
 * Wait up to `timeout` ms for an element to be rendered.
 *
 * @param {CommonWrapper} wrapper - Root Enzyme wrapper
 * @param {string|Function} selector - Selector string or function to pass to `wrapper.find`
 * @param {number} timeout
 * @return {Promise<CommonWrapper>}
 */
export function waitForElement(wrapper, selector, timeout = 10) {
  return waitFor(
    () => {
      wrapper.update();
      const el = wrapper.find(selector);
      if (el.length === 0) {
        return null;
      }
      return el;
    },
    timeout,
    `"${selector}" to render`
  );
}

/**
 * Wait up to `timeout` milliseconds for an element to become focused.
 *
 * @example
 *   someElement.focus();
 *   await waitForElementToBeFocused(someElement)
 *
 * @param {HTMLElement} element
 * @param {number} [timeout]
 */
export async function waitForElementToBeFocused(
  element,
  timeout = DEFAULT_TIMEOUT
) {
  // Catch common errors such as calling this function with a `null` value or
  // failing to render the element into `document.body` so that it can actually
  // receive focus.
  if (!(element instanceof HTMLElement)) {
    throw new Error('Element is not an `HTMLElement`');
  }

  if (!document.body.contains(element)) {
    throw new Error('Element is not part of the document');
  }

  // Spin until the element becomes focused.
  return waitFor(
    () => document.activeElement === element,
    timeout,
    `Waiting for ${element.tagName} element to be focused`
  );
}
