import classnames from 'classnames';

/**
 * @typedef ContentFrameProps
 * @prop {string} url
 * @prop {import('preact').Ref<HTMLIFrameElement>} [iframeRef]
 */

/**
 * An iframe that displays the content of an assignment.
 *
 * @param {ContentFrameProps} props
 */
export default function ContentFrame({ url, iframeRef }) {
  return (
    <iframe
      ref={iframeRef}
      className={classnames(
        // It's important that this content render full width and grow to fill
        // available flex space. n.b. It may be rendered together with grading
        // controls
        'w-full grow',
        'hyp-u-border'
      )}
      src={url}
      title="Course content with Hypothesis annotation viewer"
    />
  );
}
