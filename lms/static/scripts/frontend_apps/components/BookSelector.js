import {
  IconButton,
  SvgIcon,
  TextInput,
  TextInputWithButton,
  Thumbnail,
} from '@hypothesis/frontend-shared';
import { createElement } from 'preact';
import { useRef, useState } from 'preact/hooks';

import { useService, VitalSourceService } from '../services';

/**
 * @typedef {import('../api-types').Book} Book
 */

/**
 * @typedef BookSelectorProps
 * @prop {Book|null} selectedBook
 * @prop {(b: Book|null) => void} onSelectBook - Callback invoked when user selects a book
 */

/**
 * Component that prompts a user to enter/paste a URL to a VitalSource book.
 *
 * @param {BookSelectorProps} props
 */
export default function BookSelector({ selectedBook, onSelectBook }) {
  const vsService = useService(VitalSourceService);

  const inputRef = useRef(/** @type {HTMLInputElement|null} */ (null));
  const [isLoading, setIsLoading] = useState(false);

  const [error, setError] = useState(/** @type {string|null} */ (null));
  const previousURL = useRef(/** @type {string|null} */ (null));

  /**
   * A naive regex matcher for a VBID in a URL-like string
   *
   * @param {string} url
   * @returns {string|false}
   */
  const bookIDFromURL = url => {
    const bookIdPattern = /book\/([0-9A-Z-]+)\/?/;
    const matches = url.match(bookIdPattern);
    return !!matches && matches[1];
  };

  /**
   * Attempt to retrieve a book by bookID (vbid) via service
   *
   * @param {string} bookID
   */
  const fetchBook = bookID => {
    setIsLoading(true);
    vsService
      .fetchBook(bookID)
      .then(onSelectBook)
      .catch(err => setError(err.message))
      .finally(() => setIsLoading(false));
  };

  // Respond to changes in the input field
  const onChangeURL = () => {
    const url = inputRef.current.value;
    if (url && url === previousURL.current) {
      // Do nothing if there is no real change. This situation can arise if the
      // user "submits" a URL by typing "Enter" and then interacts elsewhere in
      // the UI (a spurious change event can be triggered).
      // This prevents reloading the same book.
      return;
    }
    previousURL.current = url;

    // Reset selected book, if any
    onSelectBook(null);
    setError(null);

    if (url) {
      // Don't try to fetch, or set any errors, if the input field is empty
      const bookID = bookIDFromURL(url);
      if (!bookID) {
        setError("That doesn't look like a VitalSource book URL");
        return;
      }
      fetchBook(bookID);
    }
  };

  // Capture "Enter" and make sure it does not submit the whole shebang
  /** @param {KeyboardEvent} event */
  const onKeyDown = event => {
    let handled = false;
    if (event.key === 'Enter') {
      handled = true;
      onChangeURL();
    }
    if (handled) {
      event.preventDefault();
      event.stopPropagation();
    }
  };

  return (
    <div className="hyp-u-layout-row hyp-u-horizontal-spacing BookSelector">
      <div className="BookSelector__thumbnail">
        <Thumbnail isLoading={isLoading}>
          {selectedBook && (
            <img
              alt={`Book cover for ${selectedBook.title}`}
              src={selectedBook.cover_image}
              data-testid="cover-image"
            />
          )}
        </Thumbnail>
      </div>
      <div className="hyp-u-stretch hyp-u-vertical-spacing--3">
        <div>Paste a link to the VitalSource book you&apos;d like to use:</div>

        <TextInputWithButton>
          <TextInput
            error={!!error}
            inputRef={inputRef}
            onChange={onChangeURL}
            onKeyDown={onKeyDown}
            placeholder="e.g. https://bookshelf.vitalsource.com/#/book/012345678..."
          />
          <IconButton
            icon="arrow-right"
            variant="dark"
            onClick={onChangeURL}
            title="Find book"
          />
        </TextInputWithButton>

        {selectedBook && (
          <div className="hyp-u-layout-row--center hyp-u-horizontal-spacing">
            <SvgIcon name="check" className="hyp-u-color--success" />
            <div className="hyp-u-stretch">
              <strong>
                <em>{selectedBook.title}</em>
              </strong>
            </div>
          </div>
        )}

        {error && (
          <div className="hyp-u-layout-row--center hyp-u-horizontal-spacing hyp-u-color--error">
            <SvgIcon name="cancel" />
            <div className="hyp-u-stretch">{error}</div>
          </div>
        )}
      </div>
    </div>
  );
}
