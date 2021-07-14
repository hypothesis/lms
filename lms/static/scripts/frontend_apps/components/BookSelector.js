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
import { bookIDFromURL } from '../utils/vitalsource';

/**
 * @typedef {import('../api-types').Book} Book
 *
 * @typedef BookSelectorProps
 * @prop {Book|null} selectedBook - The currently-selected book, if any
 * @prop {(b: Book|null) => void} onSelectBook - Callback invoked when a book
 *   corresponding to a user-entered VitalSource URL is successfully fetched.
 */

/**
 * Prompt a user to paste a URL to a VitalSource book. The pasted URL is parsed
 * for a VitalSource book identifier (VBID, or `bookID`), and an attempt made to
 * fetch book metadata corresponding to that ID using the vitalsource service.
 * Renders a thumbnail of the book cover and the book title when a book is
 * loaded/found.
 *
 * @param {BookSelectorProps} props
 */
export default function BookSelector({ selectedBook, onSelectBook }) {
  const vsService = useService(VitalSourceService);

  const inputRef = useRef(/** @type {HTMLInputElement|null} */ (null));

  // is a request in-flight via the vitalsource service?
  const [isLoadingBook, setIsLoadingBook] = useState(false);

  // Holds an error message corresponding to client-side validation of the
  // input field or a caught API error
  const [error, setError] = useState(/** @type {string|null} */ (null));

  // The last value of the URL-entry text input
  const previousURL = useRef(/** @type {string|null} */ (null));

  /**
   * Attempt to retrieve a book by bookID (vbid) via service
   *
   * @param {string} bookID
   */
  const fetchBook = async bookID => {
    if (isLoadingBook) {
      return;
    }
    setIsLoadingBook(true);
    try {
      const book = await vsService.fetchBook(bookID);
      onSelectBook(book);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoadingBook(false);
    }
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

    // Reset selected book, if any, and clear errors
    if (selectedBook) {
      onSelectBook(null);
    }
    setError(null);

    if (!url) {
      // If the field is empty, there's nothing to parse or fetch
      return;
    }

    const bookID = bookIDFromURL(url);
    if (!bookID) {
      setError("That doesn't look like a VitalSource book link");
      return;
    }
    fetchBook(bookID);
  };

  /**
   * Capture "Enter" keystrokes, and avoid submitting the entire parent `<form>`
   *
   * TODO: A subsequent "Enter" keystroke after a book is successfully loaded,
   * and there have been no changes to the pasted URL, should "confirm" the book
   * and move to the chapter-selection step. See
   * https://github.com/hypothesis/lms/issues/2952
   *
   * @param {KeyboardEvent} event */
  const onKeyDown = event => {
    if (event.key === 'Enter') {
      onChangeURL();
      event.preventDefault();
      event.stopPropagation();
    }
  };

  return (
    <div className="hyp-u-layout-row hyp-u-horizontal-spacing BookSelector">
      <div className="BookSelector__thumbnail">
        <Thumbnail isLoading={isLoadingBook}>
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
            disabled={isLoadingBook}
            hasError={!!error}
            inputRef={inputRef}
            name="vitalSourceURL"
            onChange={onChangeURL}
            onKeyDown={onKeyDown}
            placeholder="e.g. https://bookshelf.vitalsource.com/#/book/012345678..."
          />
          <IconButton
            disabled={isLoadingBook}
            icon="arrow-right"
            variant="dark"
            onClick={onChangeURL}
            title="Find book"
          />
        </TextInputWithButton>

        {selectedBook && (
          <div
            className="hyp-u-layout-row--center hyp-u-horizontal-spacing"
            data-testid="selected-book"
          >
            <SvgIcon name="check" className="hyp-u-color--success" />
            <div className="hyp-u-stretch">
              <strong>
                <em>{selectedBook.title}</em>
              </strong>
            </div>
          </div>
        )}

        {error && (
          <div
            className="hyp-u-layout-row--center hyp-u-horizontal-spacing hyp-u-color--error"
            data-testid="error-message"
          >
            <SvgIcon name="cancel" />
            <div className="hyp-u-stretch">{error}</div>
          </div>
        )}
      </div>
    </div>
  );
}
