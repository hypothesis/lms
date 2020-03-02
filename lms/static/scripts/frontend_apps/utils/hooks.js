import { useState } from 'preact/hooks';

// Global counter used to create a unique ids
let idCounter = 0;

/**
 * Creates a unique id attribute value. Each time useUniqueId() is called,
 * the numerical suffix value increments by 1.
 *
 * @param {string} prefix
 * @return {string}
 */
function useUniqueId(prefix) {
  const [localId] = useState(() => {
    ++idCounter;
    return idCounter;
  });
  return `${prefix}${localId}`;
}

export { useUniqueId };
