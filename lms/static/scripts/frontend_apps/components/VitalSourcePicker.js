import { createElement } from 'preact';
import { useCallback, useEffect, useState } from 'preact/hooks';

import { apiCall } from '../utils/api';

import BookList from './BookList';
import Button from './Button';
import ChapterList from './ChapterList';
import Dialog from './Dialog';
import ErrorDisplay from './ErrorDisplay';

/**
 * @typedef {import('../api-types').Chapter} Chapter
 * @typedef {import('../api-types').Book} Book
 *
 * @typedef VitalSourcePickerProps
 * @prop {string} authToken
 * @prop {() => any} onCancel
 * @prop {(b: Book, c: Chapter) => any} onSelectBook
 */

/**
 * A dialog that allows the user to select a book from VitalSource
 *
 * @param {VitalSourcePickerProps} props
 */
export default function VitalSourcePicker({
  authToken,
  onCancel,
  onSelectBook,
}) {
  const [bookList, setBookList] = useState(/** @type {Book[]|null} */ (null));
  const [tableOfContents, setTableOfContents] = useState(
    /** @type {Chapter[]|null} */ (null)
  );
  const [book, setBook] = useState(/** @type {Book|null} */ (null));
  const [chapter, setChapter] = useState(/** @type {Chapter|null} */ (null));
  const [step, setStep] = useState(
    /** @type {'select-book'|'select-chapter'} */ ('select-book')
  );
  const [error, setError] = useState(/** @type {Error|null} */ (null));

  const confirmBook = useCallback(book => {
    setBook(book);
    setTableOfContents(null);
    setStep('select-chapter');
  }, []);

  const confirmChapter = useCallback(
    chapter => {
      onSelectBook(/** @type {Book} */ (book), chapter);
    },
    [book, onSelectBook]
  );

  useEffect(() => {
    if (step === 'select-book' && !bookList) {
      apiCall({ authToken, path: '/api/vitalsource/books' })
        .then(setBookList)
        .catch(setError);
    } else if (step === 'select-chapter' && !tableOfContents) {
      const currentBook = /** @type {Book} */ (book);
      apiCall({
        authToken,
        path: `/api/vitalsource/books/${currentBook.id}/toc`,
      })
        .then(setTableOfContents)
        .catch(setError);
    }
  }, [authToken, book, bookList, step, tableOfContents]);

  const canSubmit =
    (step === 'select-book' && book) || (step === 'select-chapter' && chapter);

  const goBack = () => {
    setStep('select-book');
    setChapter(null);
  };

  return (
    <Dialog
      onBack={step !== 'select-book' ? goBack : null}
      onCancel={onCancel}
      title="Select book from VitalSource"
      buttons={[
        <Button
          key="submit"
          label={step === 'select-book' ? 'Select book' : 'Select chapter'}
          disabled={!canSubmit}
          onClick={() => {
            if (step === 'select-book') {
              confirmBook(book);
            } else if (step === 'select-chapter') {
              confirmChapter(chapter);
            }
          }}
        />,
      ]}
      minWidth="75vw"
      minHeight="70vh"
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
          chapters={tableOfContents || []}
          isLoading={!tableOfContents}
          selectedChapter={chapter}
          onSelectChapter={setChapter}
          onUseChapter={confirmChapter}
        />
      )}
      {error && <ErrorDisplay message="Unable to fetch books" error={error} />}
    </Dialog>
  );
}
