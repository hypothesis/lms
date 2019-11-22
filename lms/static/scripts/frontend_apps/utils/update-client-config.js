/**
 * Updates the js-hypothesis-config in the DOM.
 *
 * @param {Object} config - New settings to apply to the config.
 */
export function updateClientConfig(config) {
  const sidebarConfigEl = document.querySelector('.js-hypothesis-config');
  const sidebarConfig = JSON.parse(sidebarConfigEl.text);
  sidebarConfigEl.text = JSON.stringify({
    ...sidebarConfig,
    ...config,
  });
}
/**
 * Removes specified key values from the js-hypothesis-config.
 *
 * @param {Array} keys - Root level config keys to remove.
 */

export function removeClientConfig(keys) {
  const sidebarConfigEl = document.querySelector('.js-hypothesis-config');
  const sidebarConfig = JSON.parse(sidebarConfigEl.text);
  // Remove config values with a matching key.
  keys.forEach(key => {
    delete sidebarConfig[key];
  });
  sidebarConfigEl.text = JSON.stringify({
    ...sidebarConfig,
  });
}
