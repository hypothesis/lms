import { Button, ModalDialog } from '@hypothesis/frontend-shared/lib/next';
import classnames from 'classnames';
import { useCallback, useEffect, useState } from 'preact/hooks';

import type { Book, Chapter } from '../api-types';
import { useService, VitalSourceService } from '../services';
import BookSelector from './BookSelector';
import ChapterList from './ChapterList';
import ErrorDisplay from './ErrorDisplay';

export type BookPickerProps = {
  onCancel: () => void;
  /** Callback invoked when both a book and chapter have been selected */
  onSelectBook: (b: Book, c: Chapter) => void;
};

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
 * Note: The component logic is consistent about using the terminology of
 * "chapter" for content segments in a VitalSource eBook, but presents this
 * to the user as "location" and other slightly less precise language.
 */
export default function BookPicker({
  onCancel,
  onSelectBook,
}: BookPickerProps) {
  const vsService = useService(VitalSourceService);

  const [chapterList, setChapterList] = useState<Chapter[] | null>(null);
  const [book, setBook] = useState<Book | null>(null);
  const [chapter, setChapter] = useState<Chapter | null>(null);
  const [step, setStep] = useState<'select-book' | 'select-chapter'>(
    'select-book'
  );
  const [error, setError] = useState<Error | null>(null);

  const confirmBook = useCallback((book: Book) => {
    setBook(book);
    setChapterList(null);
    setStep('select-chapter');
  }, []);

  const confirmChapter = useCallback(
    (chapter: Chapter) => {
      onSelectBook(book!, chapter);
    },
    [book, onSelectBook]
  );

  useEffect(() => {
    if (step === 'select-chapter' && !chapterList) {
      const currentBook = book!;
      vsService
        .fetchChapters(currentBook.id)
        .then(setChapterList)
        .catch(setError);
    }
  }, [book, step, chapterList, vsService]);

  const canSubmit =
    (step === 'select-book' && book) || (step === 'select-chapter' && chapter);

  return (
    <ModalDialog
      classes={classnames(
        // Set a fix height when selecting a chapter so the modal content
        // doesn't resize after loading.
        { 'h-[25rem]': step === 'select-chapter' }
      )}
      // Opt out of Modal's automatic focus handling; route focus manually in
      // sub-components
      initialFocus={'manual'}
      onClose={onCancel}
      scrollable={false}
      title={
        step === 'select-book'
          ? 'Paste link to VitalSource book'
          : 'Pick where to start reading' // "Select a chapter"
      }
      size="lg"
      buttons={
        <>
          <Button data-testid="cancel-button" onClick={onCancel}>
            Cancel
          </Button>
          <Button
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
            {step === 'select-book' ? 'Select book' : 'Select'}
          </Button>
        </>
      }
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
              : 'Unable to fetch book contents'
          }
          error={error}
        />
      )}
    </ModalDialog>
  );
}
