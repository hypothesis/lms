import { Button, ModalDialog, Input } from '@hypothesis/frontend-shared';
import { useId, useRef, useState } from 'preact/hooks';

import { isYouTubeURL } from '../utils/youtube';
import ErrorMessage from './ErrorMessage';

export type URLPickerProps = {
  /** The initial value of the URL input field. */
  defaultURL?: string;

  onCancel: () => void;
  /** Callback invoked with the entered URL when the user accepts the dialog */
  onSelectURL: (url: string) => void;
  /** Indicates if YouTube transcript annotations are enabled */
  youtubeEnabled?: boolean;
};

/**
 * A dialog that allows the user to enter or paste the URL of a web page or
 * PDF file to use for an assignment.
 */
export default function URLPicker({
  defaultURL = '',
  onCancel,
  onSelectURL,
  youtubeEnabled = false,
}: URLPickerProps) {
  const input = useRef<HTMLInputElement | null>(null);
  const form = useRef<HTMLFormElement | null>(null);
  const errorId = useId();

  // Holds an error message corresponding to client-side validation of the
  // input field
  const [error, setError] = useState<string | null>(null);

  const submit = (event: Event) => {
    event.preventDefault();
    try {
      const rawInputValue = input.current!.value;
      const url = new URL(rawInputValue);

      if (!url.protocol.startsWith('http')) {
        if (url.protocol.startsWith('file')) {
          setError(
            'URLs that start with "file" are files on your own computer. Please use a URL that starts with "http" or "https".'
          );
        } else {
          setError('Please use a URL that starts with "http" or "https"');
        }
      } else if (isYouTubeURL(rawInputValue)) {
        // TODO If YouTube is enabled, take the user to the right content picker instead of displaying an error
        //      instructing how to do it manually
        setError(
          youtubeEnabled
            ? 'To annotate a video, go back and choose the YouTube option.'
            : 'Annotating YouTube videos has been disabled at your organisation.'
        );
      } else {
        onSelectURL(input.current!.value);
      }
    } catch (e) {
      setError('Please enter a URL, e.g. "https://www.example.com"');
    }
  };

  return (
    <ModalDialog
      title="Enter URL"
      onClose={onCancel}
      buttons={[
        <Button data-testid="cancel-button" key="cancel" onClick={onCancel}>
          Cancel
        </Button>,
        <Button
          data-testid="submit-button"
          key="submit"
          onClick={submit}
          variant="primary"
        >
          Submit
        </Button>,
      ]}
      initialFocus={input}
    >
      <div className="space-y-4">
        <p>Enter the URL of any publicly available web page or PDF:</p>
        <form
          ref={form}
          className="flex flex-row items-center space-x-2"
          onSubmit={submit}
        >
          <label htmlFor="url">URL: </label>

          <Input
            aria-label="Enter URL to web page or PDF"
            classes="grow"
            aria-labelledby={errorId}
            defaultValue={defaultURL}
            feedback={error ? 'error' : undefined}
            elementRef={input}
            name="url"
            placeholder="e.g. https://example.com/article.pdf"
            required
          />
        </form>
        {/** setting a height here "preserves space" for this error display
         * and prevents the dialog size from jumping when an error is rendered */}
        <ErrorMessage error={error} className="h-4 min-h-4" id={errorId} />
      </div>
    </ModalDialog>
  );
}
