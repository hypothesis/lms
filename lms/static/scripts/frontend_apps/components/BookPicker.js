import { LabeledButton } from '@hypothesis/frontend-shared';
import { createElement } from 'preact';
import { useCallback, useEffect, useState } from 'preact/hooks';

import { fetchBooks, fetchChapters } from '../utils/api';

import BookList from './BookList';
import ChapterList from './ChapterList';
import Dialog from './Dialog';
import ErrorDisplay from './ErrorDisplay';

/**
 * @typedef {import('../api-types').Chapter} Chapter
 * @typedef {import('../api-types').Book} Book
 *
 * @typedef BookPickerProps
 * @prop {string} authToken
 * @prop {() => any} onCancel
 * @prop {(b: Book, c: Chapter) => any} onSelectBook
 */

/**
 * A dialog that allows the user to select a book from VitalSource
 *
 * @param {BookPickerProps} props
 */
export default function BookPicker({ authToken, onCancel, onSelectBook }) {
  const [bookList, setBookList] = useState(/** @type {Book[]|null} */ (null));
  const [chapterList, setChapterList] = useState(
    /** @type {Chapter[]|null} */ (null)
  );
  const [book, setBook] = useState(/** @type {Book|null} */ (null));
  const [chapter, setChapter] = useState(/** @type {Chapter|null} */ (null));
  const [step, setStep] = useState(
    /** @type {'select-book'|'select-chapter'} */ ('select-book')
  );
  const [error, setError] = useState(/** @type {Error|null} */ (null));

  /** @type {(b: Book) => void} */
  const confirmBook = useCallback(book => {
    setBook(book);
    setChapterList(null);
    setStep('select-chapter');
  }, []);

  /** @type {(c: Chapter) => void} */
  const confirmChapter = useCallback(
    chapter => {
      onSelectBook(/** @type {Book} */ (book), chapter);
    },
    [book, onSelectBook]
  );

  useEffect(() => {
    if (step === 'select-book' && !bookList) {
      fetchBooks(authToken).then(setBookList).catch(setError);
    } else if (step === 'select-chapter' && !chapterList) {
      const currentBook = /** @type {Book} */ (book);
      fetchChapters(authToken, currentBook.id)
        .then(setChapterList)
        .catch(setError);
    }
  }, [authToken, book, bookList, step, chapterList]);

  const canSubmit =
    (step === 'select-book' && book) || (step === 'select-chapter' && chapter);

  return (
    <Dialog
      onCancel={onCancel}
      title="Select book from VitalSource"
      buttons={[
        <LabeledButton
          key="submit"
          data-testid="select-button"
          disabled={!canSubmit}
          onClick={() => {
            if (step === 'select-book' && book) {
              confirmBook(book);
            } else if (step === 'select-chapter' && chapter) {
              confirmChapter(chapter);
            }
          }}
          variant="primary"
        >
          {step === 'select-book' ? 'Select book' : 'Select chapter'}
        </LabeledButton>,
      ]}
    >
      {step === 'select-book' && !error && (
        <BookList
          books={bookList || []}
          isLoading={!bookList}
          selectedBook={book}
          onSelectBook={setBook}
          onUseBook={confirmBook}
        />
      )}
      {step === 'select-chapter' && !error && (
        <ChapterList
          chapters={chapterList || []}
          isLoading={!chapterList}
          selectedChapter={chapter}
          onSelectChapter={setChapter}
          onUseChapter={confirmChapter}
        />
      )}
      {error && (
        <ErrorDisplay
          message={
            step === 'select-book'
              ? 'Unable to fetch books'
              : 'Unable to fetch chapters'
          }
          error={error}
        />
      )}
    </Dialog>
  );
}
