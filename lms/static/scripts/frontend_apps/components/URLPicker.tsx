import { Button, ModalDialog } from '@hypothesis/frontend-shared';
import { useRef, useState } from 'preact/hooks';

import URLPickerForm from './URLPickerForm';

export type URLPickerProps = {
  /** The initial value of the URL input field. */
  defaultURL?: string;

  onCancel: () => void;
  /** Callback invoked with the entered URL when the user accepts the dialog */
  onSelectURL: (url: string) => void;
};

/**
 * A dialog that allows the user to enter or paste the URL of a web page or
 * PDF file to use for an assignment.
 */
export default function URLPicker({
  defaultURL = '',
  onCancel,
  onSelectURL,
}: URLPickerProps) {
  const input = useRef<HTMLInputElement | null>(null);

  // Holds an error message corresponding to client-side validation of the
  // input field
  const [error, setError] = useState<string | undefined>();

  const submit = (inputUrl: string) => {
    try {
      const url = new URL(inputUrl);
      if (!url.protocol.startsWith('http')) {
        if (url.protocol.startsWith('file')) {
          setError(
            'URLs that start with "file" are files on your own computer. Please use a URL that starts with "http" or "https".'
          );
        } else {
          setError('Please use a URL that starts with "http" or "https"');
        }
      } else {
        onSelectURL(inputUrl);
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
          onClick={() => submit(input.current!.value)}
          variant="primary"
        >
          Submit
        </Button>,
      ]}
      initialFocus={input}
    >
      <div className="space-y-4">
        <p>Enter the URL of any publicly available web page or PDF:</p>
        <URLPickerForm
          onSubmit={submit}
          urlPlaceholder="e.g. https://example.com/article.pdf"
          aria-label="Enter URL to web page or PDF"
          error={error}
          defaultURL={defaultURL}
          inputRef={input}
        />
      </div>
    </ModalDialog>
  );
}
