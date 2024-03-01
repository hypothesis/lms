import classnames from 'classnames';
import type { Ref } from 'preact';

export type ContentFrameProps = {
  url: string;
  iframeRef?: Ref<HTMLIFrameElement>;
};

/**
 * An iframe that displays the content of an assignment.
 */
export default function ContentFrame({ url, iframeRef }: ContentFrameProps) {
  return (
    <iframe
      ref={iframeRef}
      // Enable permissions required by Via's video player (and other content
      // too).
      //
      // "autoplay" - Enables Play button to work without first clicking on video
      // "clipboard-write *" - Used by: Via's video player, the Hypothesis client sidebar
      // "fullscreen" - Enables full-screen button in player
      allow="autoplay; clipboard-write *; fullscreen"
      className={classnames(
        // It's important that this content render full width and grow to fill
        // available flex space. n.b. It may be rendered together with grading
        // controls
        'w-full grow border',
      )}
      src={url}
      title="Course content with Hypothesis annotation viewer"
    />
  );
}
