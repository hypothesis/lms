import { Button, CheckIcon, ModalDialog } from '@hypothesis/frontend-shared';
import { useRef, useState } from 'preact/hooks';

import { InvalidArgumentError } from '../errors';
import {
  useYouTubeVideoInfo,
  validateYouTubeVideoUrl,
  videoIdFromYouTubeUrl,
} from '../utils/youtube';
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
    defaultURL && videoIdFromYouTubeUrl(defaultURL)
  );
  const [error, setError] = useState<string>();
  const { thumbnail, metadata } = useYouTubeVideoInfo(videoId);

  const verifyUrl = (inputUrl: string) => {
    try {
      const videoId = validateYouTubeVideoUrl(inputUrl);

      setVideoId(videoId);
      setError(undefined);
    } catch (e) {
      const errorMessage =
        e instanceof InvalidArgumentError
          ? e.message
          : 'Please enter a YouTube URL, e.g. "https://www.youtube.com/watch?v=cKxqzvzlnKU"';

      setVideoId(undefined);
      setError(errorMessage);
    }
  };
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
        onURLChange={verifyUrl}
        error={error}
        inputRef={inputRef}
        urlPlaceholder="e.g. https://www.youtube.com/watch?v=cKxqzvzlnKU"
        label="Enter the URL of a YouTube video:"
        defaultURL={defaultURL}
        thumbnail={thumbnail ?? { orientation: 'landscape' }}
      >
        {metadata && (
          <div className="flex flex-row space-x-2" data-testid="selected-video">
            <CheckIcon className="text-green-success" />
            <div className="grow font-bold italic">
              {metadata.title} ({metadata.channel})
            </div>
          </div>
        )}
      </URLFormWithPreview>
    </ModalDialog>
  );
}
