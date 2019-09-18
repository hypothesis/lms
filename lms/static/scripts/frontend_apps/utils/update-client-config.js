/**
 * Updates the js-hypothesis-config in the DOM.
 *
 * @param {Object} config - New settings to apply to the config
 */
export default function(config) {
  const sidebarConfigEl = document.querySelector('.js-hypothesis-config');
  const sidebarConfig = JSON.parse(sidebarConfigEl.text);
  sidebarConfigEl.text = JSON.stringify({
    ...sidebarConfig,
    ...config,
  });
}
