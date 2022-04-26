import { useEffect, useRef } from 'preact/hooks';

import ContentFrame from './ContentFrame';

/**
 * @typedef VitalSourceBookViewerProps
 * @prop {string} launchUrl - Launch URL for the book viewer
 * @prop {Record<string,string>} [launchParams] - If using a form submission
 *   to launch the book viewer, the form fields
 * @prop {(f: HTMLFormElement) => void} [willSubmitLaunchForm] - Test hook
 */

/**
 * Render the VitalSource book viewer application in an iframe.
 *
 * Depending on the authentication method, this may load the book viewer
 * directly in an iframe, or may create a temporary iframe with a form which
 * is then immediately submitted.
 *
 * @param {VitalSourceBookViewerProps} props
 */
export default function VitalSourceBookViewer({
  launchParams,
  launchUrl,
  willSubmitLaunchForm,
}) {
  const iframe = /** @type {{ current: HTMLIFrameElement }} */ (useRef());

  useEffect(() => {
    if (!launchParams) {
      return;
    }

    const iframeDoc = /** @type {Document} */ (iframe.current.contentDocument);
    const launchForm = iframeDoc.createElement('form');

    launchForm.method = 'POST';
    launchForm.action = launchUrl;

    Object.entries(launchParams).forEach(([key, value]) => {
      const field = iframeDoc.createElement('input');
      field.type = 'hidden';
      field.name = key;
      field.value = value;
      launchForm.appendChild(field);
    });
    iframeDoc.body.appendChild(launchForm);

    // Hook for tests to observe submitted form parameters.
    willSubmitLaunchForm?.(launchForm);

    // Submit the form, triggering a navigation to the VitalSource book viewer.
    launchForm.submit();
  }, [launchParams, launchUrl, willSubmitLaunchForm]);

  if (!launchParams) {
    return <ContentFrame url={launchUrl} />;
  }
  return <ContentFrame iframeRef={iframe} url="about:blank" />;
}
