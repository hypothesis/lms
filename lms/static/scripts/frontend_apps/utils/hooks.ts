import { useEffect, useState } from 'preact/hooks';

// Global counter used to create a unique ids
let idCounter = 0;

/**
 * Creates a unique id attribute value. Each time useUniqueId() is called,
 * the numerical suffix value increments by 1.
 */
export function useUniqueId(prefix: string): string {
  const [localId] = useState(() => {
    ++idCounter;
    return idCounter;
  });
  return `${prefix}${localId}`;
}

/**
 * Set the document title.
 *
 * This must only be called by one component in any page. If multiple
 * components set the title, whichever runs last will take effect.
 */
export function useDocumentTitle(documentTitle: string) {
  useEffect(() => {
    document.title = `${documentTitle} - Hypothesis`;
  }, [documentTitle]);
}

/**
 * In development environments, set a placeholder document title at the start
 * of a navigation.
 *
 * Navigations are detected using the `navigate` event of the Navigation API.
 * https://developer.mozilla.org/en-US/docs/Web/API/Navigation_API
 *
 * This placeholder makes it more obvious when a route fails to set a
 * route-specific document title using {@link useDocumentTitle}.
 */
export function usePlaceholderDocumentTitleInDev() {
  // istanbul ignore next - not used in prod, so we don't need to test it
  useEffect(() => {
    if (process.env.NODE_ENV === 'production' || !window.navigation) {
      return () => {};
    }

    const listener = () => {
      document.title = 'PLACEHOLDER DOCUMENT TITLE';
    };
    window.navigation.addEventListener('navigate', listener);

    return () => window.navigation?.removeEventListener('navigate', listener);
  }, []);
}
