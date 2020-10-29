import { isBrowserSupported } from './browser-check';

if (!isBrowserSupported()) {
  const browserWarning = document.createElement('div');
  browserWarning.className = 'browser-check-warning';
  browserWarning.innerHTML = `
  <div>
    <b>You may need to upgrade your browser to use Hypothesis.</b>
    See <a href="https://web.hypothes.is/help/which-browsers-are-supported-by-hypothesis/" target="_blank">this support article</a> for more information.
  </div>
  <div class="u-stretch"></div>
  <button class="Button">Dismiss</button>
`;

  const dismissButton = browserWarning.querySelector('button');
  dismissButton.onclick = () => {
    browserWarning.style.display = 'none';
  };

  document.body.appendChild(browserWarning);
}
