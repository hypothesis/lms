import {
  Button,
  CancelIcon,
  Modal,
  Input,
} from '@hypothesis/frontend-shared/lib/next';

import { useRef, useState } from 'preact/hooks';

export type URLPickerProps = {
  onCancel: () => void;
  /** Callback invoked with the entered URL when the user accepts the dialog */
  onSelectURL: (url: string) => void;
};

/**
 * A dialog that allows the user to enter or paste the URL of a web page or
 * PDF file to use for an assignment.
 */
export default function URLPicker({ onCancel, onSelectURL }: URLPickerProps) {
  const input = useRef<HTMLInputElement | null>(null);
  const form = useRef<HTMLFormElement | null>(null);

  // Holds an error message corresponding to client-side validation of the
  // input field
  const [error, setError] = useState<string | null>(null);

  const submit = (event: Event) => {
    event.preventDefault();
    try {
      const url = new URL(input.current!.value);
      if (!url.protocol.startsWith('http')) {
        if (url.protocol.startsWith('file')) {
          setError(
            'URLs that start with "file" are files on your own computer. Please use a URL that starts with "http" or "https".'
          );
        } else {
          setError('Please use a URL that starts with "http" or "https"');
        }
      } else {
        onSelectURL(input.current!.value);
      }
    } catch (e) {
      setError('Please enter a URL, e.g. "https://www.example.com"');
    }
  };

  return (
    <Modal
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
            hasError={!!error}
            elementRef={input}
            name="url"
            placeholder="e.g. https://example.com/article.pdf"
            required
          />
        </form>
        {/** setting a height here "preserves space" for this error display
         * and prevents the dialog size from jumping when an error is rendered */}
        <div
          className="h-4 flex flex-row items-center space-x-1 text-red-error"
          data-testid="error-message"
        >
          {!!error && (
            <>
              <CancelIcon />
              <div className="grow">{error}</div>
            </>
          )}
        </div>
      </div>
    </Modal>
  );
}
