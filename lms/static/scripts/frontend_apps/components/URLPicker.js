import { createElement } from 'preact';
import { useRef, useState } from 'preact/hooks';

import Button from './Button';
import Dialog from './Dialog';
import ValidationMessage from './ValidationMessage';

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
  const input = useRef(/** @type {HTMLInputElement|null} */ (null));
  const form = useRef(/** @type {HTMLFormElement|null} */ (null));
  // Is there a validation error message to show?
  const [showValidationError, setValidationError] = useState(false);
  // The actual validation error message.
  const [validationMessage, setValidationMessage] = useState('');

  /** @param {Event} event */
  const submit = event => {
    event.preventDefault();

    if (form.current.checkValidity()) {
      onSelectURL(input.current.value);
    } else {
      setValidationMessage('A valid URL is required');
      setValidationError(true);
    }
  };

  /**
   * If any input is detected, close the ValidationMessage.
   */
  const handleKeyDown = () => {
    setValidationError(false);
  };

  const submitButton = (
    <span className="URLPicker__buttons">
      {validationMessage && (
        <ValidationMessage
          message={validationMessage}
          open={showValidationError}
          onClose={() => {
            // Sync up the state when the ValidationMessage is closed
            setValidationError(false);
          }}
        />
      )}
      <Button key="submit" label="Submit" onClick={submit} />
    </span>
  );

  return (
    <Dialog
      contentClass="URLPicker"
      title="Enter URL"
      onCancel={onCancel}
      buttons={[submitButton]}
      initialFocus={input}
    >
      <p>Enter the URL of any publicly available web page or PDF.</p>
      <form ref={form} className="u-flex-row" onSubmit={submit}>
        <label className="label" htmlFor="url">
          URL:{' '}
        </label>
        <input
          onInput={handleKeyDown}
          className="u-stretch u-cross-stretch"
          name="path"
          type="url"
          placeholder="https://example.com/article.pdf"
          required={true}
          ref={input}
        />
      </form>
    </Dialog>
  );
}
