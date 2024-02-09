import {
  ArrowRightIcon,
  IconButton,
  InputGroup,
  Input,
  Thumbnail,
} from '@hypothesis/frontend-shared';
import classNames from 'classnames';
import { useEffect, useId, useRef, useState } from 'preact/hooks';

import type { Book } from '../api-types';
import { formatErrorMessage } from '../errors';
import { useService, VitalSourceService } from '../services';
import { extractBookID } from '../utils/vitalsource';
import UIMessage from './UIMessage';

export type BookSelectorProps = {
  /** The currently-selected book, if any */
  selectedBook: Book | null;

  /**
   * Callback to confirm a fetched book and move on to the chapter-selection
   * step. This is subsequent to selecting a book.
   */
  onConfirmBook: (b: Book) => void;

  /**
   * Callback invoked when a book corresponding to a user-entered VitalSource
   * URL is successfully fetched.
   */
  onSelectBook: (b: Book | null) => void;
};

/**
 * Prompt a user to paste a URL to a VitalSource book. The pasted URL is parsed
 * for a VitalSource book identifier (VBID, or `bookID`), and an attempt made to
 * fetch book metadata corresponding to that ID using the vitalsource service.
 * Renders a thumbnail of the book cover and the book title when a book is
 * loaded/found.
 */
export default function BookSelector({
  selectedBook,
  onConfirmBook,
  onSelectBook,
}: BookSelectorProps) {
  const vsService = useService(VitalSourceService);

  const inputRef = useRef<HTMLInputElement | null>(null);
  const errorId = useId();

  // is a request in-flight via the vitalsource service?
  const [isLoadingBook, setIsLoadingBook] = useState(false);

  // Holds an error message corresponding to client-side validation of the
  // input field or a caught API error
  const [error, setError] = useState<string | null>(null);

  // The last value of the URL-entry text input
  const previousURL = useRef<string | null>(null);

  /**
   * Fetch a book using a VBID
   */
  const fetchBook = async (bookID: string) => {
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
   */
  const onUpdateURL = (confirmSelectedBook = false) => {
    const url = inputRef.current!.value;
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
    inputRef.current!.focus();
    // We only want to run this effect once.
    //
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * Capture "Enter" keystrokes, and avoid submitting the entire parent `<form>`
   * If "Enter" is pressed and there is already a valid, fetched book, and no
   * changes to the URL entered in the text input, "confirm" the book selection
   * and move to the select-chapter step.
   */
  const onKeyDown = (event: KeyboardEvent) => {
    if (event.key === 'Enter') {
      onUpdateURL(true /* confirmSelectedBook */);
      event.preventDefault();
      event.stopPropagation();
    }
  };

  return (
    <div className="flex flex-row space-x-3">
      <div className="w-[132px]">
        <Thumbnail loading={isLoadingBook} ratio="4/5">
          {selectedBook && (
            <img
              alt={`Book cover for ${selectedBook.title}`}
              className={classNames(
                // Use `object-fit: contain` instead of default `cover`
                // This ensures none of the image is cropped
                // TODO: Remove !-rule when
                // https://github.com/hypothesis/frontend-shared/issues/842 is
                // resolved
                '!object-contain'
              )}
              src={selectedBook.cover_image}
              data-testid="cover-image"
            />
          )}
        </Thumbnail>
      </div>
      <div className="grow space-y-2">
        <p>
          Paste a link or ISBN for the VitalSource book you&apos;d like to use:
        </p>

        <InputGroup>
          <Input
            aria-label="VitalSource URL or ISBN"
            data-testid="vitalsource-input"
            feedback={error ? 'error' : undefined}
            elementRef={inputRef}
            name="vitalSourceURL"
            onChange={() => onUpdateURL(false /* confirmSelectedBook */)}
            onKeyDown={onKeyDown}
            placeholder="e.g. https://bookshelf.vitalsource.com/#/books/012345678..."
            readOnly={isLoadingBook}
            spellcheck={false}
            aria-describedby={errorId}
          />
          <IconButton
            icon={ArrowRightIcon}
            onClick={() => onUpdateURL(false /* confirmSelectedBook */)}
            title="Find book"
            variant="dark"
          />
        </InputGroup>

        {selectedBook && (
          <UIMessage status="success" data-testid="selected-book">
            <span className="font-bold italic">{selectedBook.title}</span>
          </UIMessage>
        )}

        {error && (
          <UIMessage status="error" data-testid="error-message" id={errorId}>
            {error}
          </UIMessage>
        )}
      </div>
    </div>
  );
}
