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
 * Updates page title with provided one
 */
export function usePageTitle(pageTitle: string) {
  useEffect(() => {
    document.title = pageTitle;
  }, [pageTitle]);
}
