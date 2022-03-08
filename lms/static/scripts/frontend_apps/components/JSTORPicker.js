import {
  Icon,
  IconButton,
  LabeledButton,
  Modal,
  Thumbnail,
  TextInputWithButton,
  TextInput,
} from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import { useRef, useState } from 'preact/hooks';

import { toJSTORUrl } from '../utils/jstor';

/**
 * @typedef JSTORPickerProps
 * @prop {() => void} onCancel
 * @prop {(url: string) => void} onSelectURL - Callback to set the assignment's
 *   content to a JSTOR article URL
 */

/**
 * A picker that allows a user to enter a URL corresponding to a JSTOR article.
 *
 * @param {JSTORPickerProps} props
 */
export default function JSTORPicker({ onCancel, onSelectURL }) {
  const [error, setError] = useState(/** @type {string|null} */ (null));
  const [selectedURL, setSelectedURL] = useState(
    /** @type {string|null} */ (null)
  );

  const inputRef = /** @type {{ current: HTMLInputElement }} */ (useRef());
  // The last value of the URL-entry text input
  const previousURL = useRef(/** @type {string|null} */ (null));

  const confirmSelection = () => {
    if (selectedURL) {
      onSelectURL(selectedURL);
    }
  };

  /**
   * @param {boolean} [confirmSelectedUrl=false]
   */
  const onUpdateURL = (confirmSelectedUrl = false) => {
    const url = inputRef?.current?.value;
    if (url && url === previousURL.current) {
      if (confirmSelectedUrl) {
        confirmSelection();
      }
      return;
    }

    previousURL.current = url;
    setSelectedURL(null);

    if (!url) {
      // If the field is empty, there's nothing to do
      return;
    }

    const jstorUrl = toJSTORUrl(url);

    if (jstorUrl) {
      setError(null);
      setSelectedURL(jstorUrl);
    } else {
      setError("That doesn't look like a JSTOR article link");
    }
  };

  /**
   * Capture "Enter" keystrokes, and avoid submitting the entire parent `<form>`
   *
   * @param {KeyboardEvent} event
   */
  const onKeyDown = event => {
    if (event.key === 'Enter') {
      onUpdateURL(true /* confirmSelectedUrl */);
      event.preventDefault();
      event.stopPropagation();
    }
  };

  return (
    <Modal
      initialFocus={inputRef}
      onCancel={onCancel}
      contentClass={classnames('LMS-Dialog LMS-Dialog--wide')}
      title="Select JSTOR article"
      buttons={[
        <LabeledButton
          data-testid="select-button"
          disabled={!selectedURL}
          key="submit"
          onClick={confirmSelection}
          variant="primary"
        >
          Submit
        </LabeledButton>,
      ]}
    >
      <div className="flex flex-row space-x-3">
        <Thumbnail classes="w-32 h-40" />
        <div className="space-y-2 grow">
          <p>Paste a link to the JSTOR article you&apos;d like to use:</p>

          <TextInputWithButton>
            <TextInput
              inputRef={inputRef}
              name="jstorURL"
              onChange={() => onUpdateURL(false /* confirmSelectedUrl */)}
              onKeyDown={onKeyDown}
              placeholder="e.g. https://www.jstor.org/stable/1234"
            />
            <IconButton
              icon="arrowRight"
              onClick={() => onUpdateURL(false /* confirmSelectedUrl */)}
              variant="dark"
              title="Find article"
            />
          </TextInputWithButton>

          {selectedURL && (
            <div
              className="flex flex-row items-center space-x-2"
              data-testid="selected-book"
            >
              <Icon name="check" classes="text-green-success" />
              <div className="grow font-bold italic">JSTOR article</div>
            </div>
          )}

          {error && (
            <div
              className="flex flex-row items-center space-x-2 text-red-error"
              data-testid="error-message"
            >
              <Icon name="cancel" />
              <div className="grow">{error}</div>
            </div>
          )}
        </div>
      </div>
    </Modal>
  );
}
