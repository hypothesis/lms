import { createElement } from 'preact';
import { useEffect, useRef } from 'preact/hooks';

/**
 * @typedef VitalSourceBookViewerProps
 * @prop {string} launchUrl
 * @prop {Object.<string,string>} launchParams
 */

/**
 * @param {VitalSourceBookViewerProps} props
 */
export default function VitalSourceBookViewer({ launchParams, launchUrl }) {
  const iframe = useRef(/** @type {HTMLIFrameElement|null} */ (null));

  useEffect(() => {
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
    launchForm.submit();
  }, [launchParams, launchUrl]);

  return (
    <iframe
      ref={iframe}
      width="100%"
      height="100%"
      title="Course content with Hypothesis annotation viewer"
      src="about:blank"
    />
  );
}
