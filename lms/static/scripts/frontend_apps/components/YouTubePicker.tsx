import { Button, CheckIcon, ModalDialog } from '@hypothesis/frontend-shared';
import { useEffect, useRef, useState } from 'preact/hooks';

import { useYouTubeVideoInfo, videoIdFromYouTubeURL } from '../utils/youtube';
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
  const [videoId, setVideoId] = useState(
    (defaultURL && videoIdFromYouTubeURL(defaultURL)) || null
  );
  const [error, setError] = useState<string>();
  const resetToInitialState = () => {
    setVideoId(null);
    setError(undefined);
  };
  const videoInfo = useYouTubeVideoInfo(videoId);
  const transitionToErrorState = (
    errorMessage = 'URL must be a YouTube video, e.g. "https://www.youtube.com/watch?v=cKxqzvzlnKU"'
  ) => {
    setVideoId(null);
    setError(errorMessage);
  };
  const transitionToSuccessState = (videoId: string) => {
    setVideoId(videoId);
    setError(undefined);
  };

  const verifyURL = (inputURL: string) => {
    const videoId = videoIdFromYouTubeURL(inputURL);
    if (videoId) {
      transitionToSuccessState(videoId);
    } else {
      transitionToErrorState();
    }
  };
  const confirmSelection = () => {
    if (videoId) {
      onSelectURL(`youtube://${videoId}`);
    }
  };

  // Display an error if a videoId was resolved (meaning, the URL fulfils the right pattern), but the server returns
  // an error
  useEffect(() => {
    if (videoInfo.error) {
      transitionToErrorState(
        videoInfo.error === 'video_not_found'
          ? 'Provided URL does not belong to a valid YouTube video'
          : undefined
      );
    }
  }, [videoInfo]);

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
          disabled={!videoId}
          key="submit"
          onClick={confirmSelection}
          variant="primary"
        >
          Continue
        </Button>,
      ]}
    >
      <URLFormWithPreview
        onURLChange={verifyURL}
        onInput={resetToInitialState}
        error={error}
        inputRef={inputRef}
        urlPlaceholder="e.g. https://www.youtube.com/watch?v=cKxqzvzlnKU"
        label="Enter the URL of a YouTube video:"
        defaultURL={defaultURL}
        thumbnail={{
          isLoading: videoInfo.isLoading,
          image: videoInfo.image,
          alt: 'Youtube video',
          orientation: 'landscape',
        }}
      >
        {videoInfo.title && videoInfo.channel && (
          <div className="flex flex-row space-x-2" data-testid="selected-video">
            <CheckIcon className="text-green-success" />
            <div className="grow font-bold italic">
              {videoInfo.title} ({videoInfo.channel})
            </div>
          </div>
        )}
      </URLFormWithPreview>
    </ModalDialog>
  );
}
