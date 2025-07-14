let unsavedCount = 0;

function preventUnload(e: BeforeUnloadEvent) {
  // `preventDefault` is the modern API for preventing unload.
  e.preventDefault();

  // Setting `returnValue` to a truthy value is a legacy method needed for
  // Firefox. Note that in Chrome, reading `returnValue` will return false
  // afterwards.
  e.returnValue = true;
}

/**
 * Return true if an alert will currently be triggered if the tab is closed.
 */
export function hasUnsavedChanges() {
  return unsavedCount > 0;
}

/**
 * Increment the count of unsaved changes.
 *
 * When the count is non-zero, a "beforeunload" event handler is used to trigger
 * an alert if the user closes the tab.
 */
export function incrementUnsavedCount() {
  unsavedCount += 1;
  if (unsavedCount === 1) {
    window.addEventListener('beforeunload', preventUnload);
  }
}

/**
 * Decrement the count of unsaved changes.
 *
 * When this count goes to zero, alerts when unloading the tab are disabled.
 */
export function decrementUnsavedCount() {
  if (unsavedCount === 0) {
    return;
  }
  unsavedCount -= 1;
  if (unsavedCount === 0) {
    window.removeEventListener('beforeunload', preventUnload);
  }
}
