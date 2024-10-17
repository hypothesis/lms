import {
  Button,
  ModalDialog,
  Input,
  useValidateOnSubmit,
} from '@hypothesis/frontend-shared';
import { useId, useRef, useState } from 'preact/hooks';

import { isYouTubeURL } from '../utils/youtube';
import UIMessage from './UIMessage';

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

  // Holds an error message corresponding to client-side validation of the
  // input field
  const [error, setError] = useState<string>();
  const errorId = useId();
  const formId = useId();

  const validateInput = () => {
    try {
      const rawInputValue = input.current!.value;
      const url = new URL(rawInputValue);

      if (!url.protocol.startsWith('http')) {
        if (url.protocol.startsWith('file')) {
          setError(
            'URLs that start with "file" are files on your own computer. Please use a URL that starts with "http" or "https".',
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
            : 'Annotating YouTube videos has been disabled at your organisation.',
        );
      } else {
        setError(undefined);
      }
    } catch {
      setError('Please enter a URL, e.g. "https://www.example.com"');
    }
  };

  const onSubmit = useValidateOnSubmit(() => {
    onSelectURL(input.current!.value);
  });

  return (
    <ModalDialog
      title="Enter URL"
      onClose={onCancel}
      closeTitle="Close URL picker"
      buttons={[
        <Button data-testid="cancel-button" key="cancel" onClick={onCancel}>
          Cancel
        </Button>,
        <Button
          data-testid="submit-button"
          form={formId}
          key="submit"
          variant="primary"
          type="submit"
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
          id={formId}
          onSubmit={onSubmit}
          noValidate // We do our own validation
        >
          <label htmlFor="url">URL: </label>
          <Input
            aria-label="Enter URL to web page or PDF"
            classes="grow"
            defaultValue={defaultURL}
            error={error}
            elementRef={input}
            name="url"
            placeholder="e.g. https://example.com/article.pdf"
            required
            aria-describedby={errorId}
            onChange={validateInput}
          />
        </form>
        {/** setting a height here "preserves space" for this error display
         * and prevents the dialog size from jumping when an error is rendered */}
        <div className="h-4 min-h-4">
          {!!error && (
            <UIMessage status="error" id={errorId}>
              {error}
            </UIMessage>
          )}
        </div>
      </div>
    </ModalDialog>
  );
}
