/**
 * Run a series of feature tests to see if the browser is new enough to support Hypothesis.
 *
 * We use feature tests to try to avoid false negatives. These are only representative,
 * not exhaustive, checks of required APIs.
 *
 * @return {boolean}
 */
export function isBrowserSupported() {
  const checks = [
    // ES APIs.
    () => Promise.resolve(),
    () => new Map(),

    // DOM API checks for APIs used by the LMS frontend and Hypothesis client.
    () => new URL(document.location.href), // URL constructor.
    () => new Request('https://hypothes.is'), // Part of the `fetch` API.
    () => document.body.prepend.name, // Element.prepend() method.
  ];

  try {
    checks.forEach(check => check());
    return true;
  } catch (err) {
    return false;
  }
}
