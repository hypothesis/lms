import { Button, ModalDialog } from '@hypothesis/frontend-shared';
import { useRef, useState } from 'preact/hooks';

import { InvalidArgumentError } from '../errors';
import { validateYouTubeVideUrl } from '../utils/youtube';
import URLPickerForm from './URLPickerForm';

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
  const [error, setError] = useState<string>();

  const onSubmit = (inputUrl: string) => {
    try {
      validateYouTubeVideUrl(inputUrl);

      // Hide any error that is currently displayed
      setError(undefined);
      onSelectURL(inputUrl);
    } catch (e) {
      const errorMessage =
        e instanceof InvalidArgumentError
          ? e.message
          : 'Please enter a YouTube URL, e.g. "https://www.youtube.com/watch?v=cKxqzvzlnKU"';
      setError(errorMessage);
    }
  };

  return (
    <ModalDialog
      title="YouTube"
      onClose={onCancel}
      initialFocus={inputRef}
      buttons={[
        <Button data-testid="cancel-button" key="cancel" onClick={onCancel}>
          Cancel
        </Button>,
        <Button
          data-testid="submit-button"
          key="submit"
          onClick={() => onSubmit(inputRef.current!.value)}
          variant="primary"
        >
          Submit
        </Button>,
      ]}
    >
      <p>Enter the URL of a YouTube video:</p>
      <URLPickerForm
        onSubmit={onSubmit}
        urlPlaceholder="e.g. https://www.youtube.com/watch?v=cKxqzvzlnKU"
        aria-label="Enter the URL of a YouTube video"
        inputRef={inputRef}
        defaultURL={defaultURL}
        error={error}
      />
    </ModalDialog>
  );
}
