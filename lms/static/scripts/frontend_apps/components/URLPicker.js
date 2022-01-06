import {
  LabeledButton,
  Modal,
  Icon,
  TextInput,
} from '@hypothesis/frontend-shared';

import { useRef, useState } from 'preact/hooks';

/**
 * @typedef URLPickerProps
 * @prop {() => any} onCancel
 * @prop {(url: string) => any} onSelectURL -
 *   Callback invoked with the entered URL when the user accepts the dialog
 */

/**
 * A dialog that allows the user to enter or paste the URL of a web page or
 * PDF file to use for an assignment.
 *
 * @param {URLPickerProps} props
 */
export default function URLPicker({ onCancel, onSelectURL }) {
  const input = /** @type {{ current: HTMLInputElement }} */ (useRef());
  const form = /** @type {{ current: HTMLFormElement }} */ (useRef());

  // Holds an error message corresponding to client-side validation of the
  // input field
  const [error, setError] = useState(/** @type {string|null} */ (null));

  /** @param {Event} event */
  const submit = event => {
    event.preventDefault();
    try {
      const url = new URL(input.current.value);
      if (!url.protocol.startsWith('http')) {
        if (url.protocol.startsWith('file')) {
          setError(
            'URLs that start with "file" are files on your own computer. Please use a URL that starts with "http" or "https".'
          );
        } else {
          setError('Please use a URL that starts with "http" or "https"');
        }
      } else {
        onSelectURL(input.current.value);
      }
    } catch (e) {
      setError('Please enter a URL, e.g. "https://www.example.com"');
    }
  };

  return (
    <Modal
      contentClass="LMS-Dialog LMS-Dialog--medium"
      title="Enter URL"
      onCancel={onCancel}
      buttons={[
        <LabeledButton key="submit" onClick={submit} variant="primary">
          Submit
        </LabeledButton>,
      ]}
      initialFocus={input}
    >
      <div className="hyp-u-vertical-spacing">
        <p>Enter the URL of any publicly available web page or PDF:</p>
        <form
          ref={form}
          className="flex flex-row items-center space-x-2"
          onSubmit={submit}
        >
          <label htmlFor="url">URL: </label>

          <TextInput
            classes="grow"
            hasError={!!error}
            inputRef={input}
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
              <Icon name="cancel" />
              <div className="grow">{error}</div>
            </>
          )}
        </div>
      </div>
    </Modal>
  );
}
