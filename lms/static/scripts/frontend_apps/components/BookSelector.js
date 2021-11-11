import {
  Icon,
  IconButton,
  TextInput,
  TextInputWithButton,
  Thumbnail,
} from '@hypothesis/frontend-shared';

import { useEffect, useRef, useState } from 'preact/hooks';

import { formatErrorMessage } from '../errors';
import { useService, VitalSourceService } from '../services';
import { extractBookID } from '../utils/vitalsource';

/**
 * @typedef {import('../api-types').Book} Book
 *
 * @typedef BookSelectorProps
 * @prop {Book|null} selectedBook - The currently-selected book, if any
 * @prop {(b: Book) => void} onConfirmBook - Callback to confirm a fetched book
 *   and move on to the chapter-selection step. This is subsequent to selecting
 *   a book.
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
export default function BookSelector({
  selectedBook,
  onConfirmBook,
  onSelectBook,
}) {
  const vsService = useService(VitalSourceService);

  const inputRef = /** @type {{ current: HTMLInputElement }} */ (useRef());

  // is a request in-flight via the vitalsource service?
  const [isLoadingBook, setIsLoadingBook] = useState(false);

  // Holds an error message corresponding to client-side validation of the
  // input field or a caught API error
  const [error, setError] = useState(/** @type {string|null} */ (null));

  // The last value of the URL-entry text input
  const previousURL = useRef(/** @type {string|null} */ (null));

  /**
   * Fetch a book using a VBID
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
      setError(formatErrorMessage(err));
    } finally {
      setIsLoadingBook(false);
    }
  };

  /**
   * Evaluate the current value in the text input (URL) and fetch book metadata.
   * Do not fetch book metadata if the value hasn't changed since last processed,
   * or is empty.
   *
   * A `true` value for `confirmSelectedBook` indicates that a book should
   * be confirmed (and move on to the select-chapter step) if the following
   * conditions are met:
   *
   *  - There have been no changes to the input's URL value since last check AND
   *  - There is a valid selected book
   *
   * This is used to allow subsequent "Enter" to submit a book that has been
   * selected/fetched already.
   *
   * @param {boolean} [confirmSelectedBook=false]
   */
  const onUpdateURL = (confirmSelectedBook = false) => {
    const url = inputRef.current.value;
    if (url && url === previousURL.current) {
      if (selectedBook && confirmSelectedBook) {
        onConfirmBook(selectedBook);
      }
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

    const bookID = extractBookID(url);
    if (!bookID) {
      setError("That doesn't look like a VitalSource book link or ISBN");
      return;
    }
    fetchBook(bookID);
  };

  useEffect(() => {
    // Focus the input field when the component is first rendered
    inputRef.current.focus();
    // We only want to run this effect once.
    //
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * Capture "Enter" keystrokes, and avoid submitting the entire parent `<form>`
   * If "Enter" is pressed and there is already a valid, fetched book, and no
   * changes to the URL entered in the text input, "confirm" the book selection
   * and move to the select-chapter step.
   *
   * @param {KeyboardEvent} event */
  const onKeyDown = event => {
    if (event.key === 'Enter') {
      onUpdateURL(true /* confirmSelectedBook */);
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
        <div>
          Paste a link or ISBN for the VitalSource book you&apos;d like to use:
        </div>

        <TextInputWithButton>
          <TextInput
            readOnly={isLoadingBook}
            hasError={!!error}
            inputRef={inputRef}
            name="vitalSourceURL"
            onChange={() => onUpdateURL(false /* confirmSelectedBook */)}
            onKeyDown={onKeyDown}
            placeholder="e.g. https://bookshelf.vitalsource.com/#/books/012345678..."
          />
          <IconButton
            icon="arrowRight"
            variant="dark"
            onClick={() => onUpdateURL(false /* confirmSelectedBook */)}
            title="Find book"
          />
        </TextInputWithButton>

        {selectedBook && (
          <div
            className="hyp-u-layout-row--center hyp-u-horizontal-spacing--2"
            data-testid="selected-book"
          >
            <Icon name="check" classes="hyp-u-color--success" />
            <div className="hyp-u-stretch BookSelector__title">
              {selectedBook.title}
            </div>
          </div>
        )}

        {error && (
          <div
            className="hyp-u-layout-row--center hyp-u-horizontal-spacing--2 hyp-u-color--error"
            data-testid="error-message"
          >
            <Icon name="cancel" />
            <div className="hyp-u-stretch">{error}</div>
          </div>
        )}
      </div>
    </div>
  );
}
