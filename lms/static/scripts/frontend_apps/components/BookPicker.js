import classnames from 'classnames';

import { LabeledButton, Modal } from '@hypothesis/frontend-shared';

import { useCallback, useEffect, useState } from 'preact/hooks';

import { useService, VitalSourceService } from '../services';

import BookSelector from './BookSelector';
import ChapterList from './ChapterList';
import ErrorDisplay from './ErrorDisplay';

/**
 * @typedef {import('../api-types').Chapter} Chapter
 * @typedef {import('../api-types').Book} Book
 *
 * @typedef BookPickerProps
 * @prop {() => void} onCancel
 * @prop {(b: Book, c: Chapter) => void} onSelectBook - Callback invoked when
 *   a book and chapter have been selected
 */

/**
 * A dialog that allows the user to select a book and chapter to use in an assignment.
 *
 * The list of available books is fetched from VitalSource, but this component
 * could be adapted to work with other book sources in future.
 *
 * The dialog has two steps: The user first chooses a book to use and then chooses
 * which chapter to use from that book. Once both are chosen the `onSelectBook`
 * callback is called.
 *
 * @param {BookPickerProps} props
 */
export default function BookPicker({ onCancel, onSelectBook }) {
  const vsService = useService(VitalSourceService);

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
    if (step === 'select-chapter' && !chapterList) {
      const currentBook = /** @type {Book} */ (book);
      vsService
        .fetchChapters(currentBook.id)
        .then(setChapterList)
        .catch(setError);
    }
  }, [book, step, chapterList, vsService]);

  const canSubmit =
    (step === 'select-book' && book) || (step === 'select-chapter' && chapter);

  return (
    <Modal
      // Opt out of Modal's automatic focus handling; route focus manually in
      // sub-components
      initialFocus={null}
      onCancel={onCancel}
      contentClass={classnames('BookPicker', {
        'BookPicker--select-chapter': step === 'select-chapter',
      })}
      title={
        step === 'select-book'
          ? 'Paste link to VitalSource book'
          : 'Select chapter'
      }
      buttons={[
        <LabeledButton
          key="submit"
          data-testid="select-button"
          disabled={!canSubmit}
          onClick={() => {
            // nb. The `book` and `chapter` checks should be redundant, as the button
            // should not be clickable if no book/chapter is selected, but they
            // keep TS happy.
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
        <BookSelector
          selectedBook={book}
          onConfirmBook={confirmBook}
          onSelectBook={setBook}
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
          description={
            step === 'select-book'
              ? 'Unable to fetch books'
              : 'Unable to fetch chapters'
          }
          error={error}
        />
      )}
    </Modal>
  );
}
