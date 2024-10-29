import type { MutableRef } from 'preact/hooks';
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
 * of a navigation to a different path.
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

    const listener = (e: NavigateEvent) => {
      const { pathname: newPath } = new URL(e.destination.url);
      const currentPath = location.pathname;

      if (currentPath !== newPath) {
        document.title = 'PLACEHOLDER DOCUMENT TITLE';
      }
    };
    window.navigation.addEventListener('navigate', listener);

    return () => window.navigation?.removeEventListener('navigate', listener);
  }, []);
}

/**
 * Determines if an element is truncated due to content or text hidden overflow
 */
export function useElementIsTruncated<T extends HTMLElement>(
  elementRef: MutableRef<T | null>,
): boolean {
  const [isTruncated, setIsTruncated] = useState(false);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) {
      return () => {};
    }

    const computeIsTruncated = () =>
      setIsTruncated(element.scrollWidth > element.clientWidth);

    // Check if element ius truncated on mount
    computeIsTruncated();
    // Re-check when the element intersects with the viewport
    const observer = new IntersectionObserver(computeIsTruncated);
    observer.observe(element);

    return () => observer.disconnect();
  }, [elementRef]);

  return isTruncated;
}
