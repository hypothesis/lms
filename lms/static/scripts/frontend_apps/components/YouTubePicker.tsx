import { Button, ModalDialog } from '@hypothesis/frontend-shared';
import { useMemo, useRef, useState } from 'preact/hooks';

import type { YouTubeVideoInfo } from '../api-types';
import { isAPIError } from '../errors';
import { urlPath, useAPIFetch } from '../utils/api';
import { videoIdFromYouTubeURL } from '../utils/youtube';
import UIMessage from './UIMessage';
import URLFormWithPreview from './URLFormWithPreview';

export type YouTubePickerProps = {
  /** The initial value of the URL input field. */
  defaultURL?: string;

  onCancel: () => void;
  /** Callback invoked with the entered URL when the user accepts the dialog */
  onSelectURL: (url: string) => void;
};

export default function YouTubePicker({
  onCancel,
  defaultURL,
  onSelectURL,
}: YouTubePickerProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [currentURL, setCurrentURL] = useState(defaultURL);
  const videoId = useMemo(
    () => (currentURL ? videoIdFromYouTubeURL(currentURL) : null),
    [currentURL]
  );
  const videoInfo = useAPIFetch<YouTubeVideoInfo>(
    videoId ? urlPath`/api/youtube/videos/${videoId}` : null
  );
  const error = useMemo(() => {
    const defaultError =
      'URL must be a YouTube video, e.g. "https://www.youtube.com/watch?v=cKxqzvzlnKU"';

    // We have a fetch error. A valid YouTube URL was set, but the API could not find the video
    if (videoInfo.error && isAPIError(videoInfo.error)) {
      return videoInfo.error.errorCode === 'youtube_video_not_found'
        ? 'Video not found'
        : defaultError;
    }

    // A URL was set, but it's not a valid YouTube URL
    if (currentURL && !videoId) {
      return defaultError;
    }

    return undefined;
  }, [currentURL, videoId, videoInfo.error]);

  const onURLChange = (inputURL: string) => setCurrentURL(inputURL);
  const resetCurrentURL = () => setCurrentURL(undefined);
  const confirmSelection = () => {
    if (videoId) {
      onSelectURL(`youtube://${videoId}`);
    }
  };

  return (
    <ModalDialog
      title="Select YouTube video"
      onClose={onCancel}
      initialFocus={inputRef}
      size="lg"
      scrollable={false}
      buttons={[
        <Button data-testid="cancel-button" key="cancel" onClick={onCancel}>
          Cancel
        </Button>,
        <Button
          data-testid="select-button"
          disabled={!videoInfo.data}
          key="submit"
          onClick={confirmSelection}
          variant="primary"
        >
          Continue
        </Button>,
      ]}
    >
      <URLFormWithPreview
        onURLChange={onURLChange}
        onInput={resetCurrentURL}
        errors={error && [error]}
        inputRef={inputRef}
        urlPlaceholder="e.g. https://www.youtube.com/watch?v=cKxqzvzlnKU"
        label="Enter the URL of a YouTube video:"
        defaultURL={defaultURL}
        thumbnail={{
          isLoading: videoInfo.isLoading,
          image: videoInfo.data?.image,
          alt: videoInfo.data?.title,
          orientation: 'landscape',
        }}
      >
        {videoInfo.data?.title && videoInfo.data.channel && (
          <UIMessage data-testid="selected-video" status="success">
            <span className="font-bold italic">
              {videoInfo.data.title} ({videoInfo.data.channel})
            </span>
          </UIMessage>
        )}
      </URLFormWithPreview>
    </ModalDialog>
  );
}
